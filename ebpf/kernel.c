#include "vmlinux.h"
#include "tracing.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>


// Some eBPF programs must be GPL licensed. This depends on program types,
// eBPF helpers used and among other things. As this eBPF program is
// integrating with tracepoints, it must be GPL.
char _license[] SEC("license") = "GPL";

struct {
  __uint(type, BPF_MAP_TYPE_HASH);
  __type(key, uint8_t);
  __type(value, struct request_type_statistic);
  __uint(max_entries, 3); // setup to match number of different keys.
} trace_map SEC(".maps");

struct {
  __uint(type, BPF_MAP_TYPE_HASH);
  __type(key, uint8_t);
  __type(value, uint64_t);
  __uint(max_entries, 1);
} debug_map SEC(".maps");

struct {
  __uint(type, BPF_MAP_TYPE_HASH);
  __type(key, struct request_key);
  __type(value, struct request_value);
  __uint(max_entries, 1024 * 8);
} issue_ts_map SEC(".maps");

struct {
  __uint(type, BPF_MAP_TYPE_HASH);
  __type(key, struct request_key);
  __type(value, struct request_value);
  __uint(max_entries, 1024 * 8);
} insert_ts_map SEC(".maps");

struct {
  __uint(type, BPF_MAP_TYPE_HASH);
  __type(key, uint64_t);
  __type(value, struct request_trace);
  __uint(max_entries, 128 * 1024 * 1024);
} lat_map SEC(".maps");

struct {
  __uint(type, BPF_MAP_TYPE_HASH);
  __type(key, uint8_t);
  __type(value, uint64_t);
  __uint(max_entries, 1);
} cache_misses SEC(".maps");

void set_comm(uint8_t target_comm[], uint8_t source_comm[]){
  for (int i = 0; i < 16; i++){
    target_comm[i] = source_comm[i];
  }
}

static __always_inline
int32_t trace_start(struct block_rq_submission *ctx, int32_t issue){
  uint64_t ts = bpf_ktime_get_ns();
  uint64_t id = bpf_get_current_pid_tgid();
  uint32_t pid = id >> 32; 
  struct request_key key = { .dev = ctx->dev, .sector = ctx->sector };
  struct request_value value = { .timestamp = ts, .nr_bytes = ctx->nr_bytes, .common_pid = pid };
  bpf_get_current_comm(&(value.comm), sizeof(value.comm));

  if (issue){
    bpf_map_update_elem(&issue_ts_map, &key, &value, 0);
  } else {
    bpf_map_update_elem(&insert_ts_map, &key, &value, 0);
  }
  
  return 0;
}

static __always_inline
int32_t trace_end(struct block_rq_complete *ctx){
  uint64_t ts = bpf_ktime_get_ns();
  struct request_value *insert_value, *issue_value;
  struct request_key key = { .dev = ctx->dev, .sector = ctx->sector };

  insert_value = bpf_map_lookup_elem(&insert_ts_map, &key);
  issue_value = bpf_map_lookup_elem(&issue_ts_map, &key);

  // If there is no issue timestamp, it has not been submitted to the device.
  if (!issue_value){
    uint64_t *current_count;
    uint16_t missed_key = MISSED_TRACES;
    current_count = bpf_map_lookup_elem(&debug_map, &missed_key);

    if (!current_count){
      uint64_t value = 1;
      bpf_map_update_elem(&debug_map, &missed_key, &value, 0);
    } else {
      (*current_count)++;
    }

    return 0;
  }

  uint64_t size = 0;
  if (insert_value && insert_value->nr_bytes) {
    size = insert_value->nr_bytes;
  }
  if (issue_value->nr_bytes && issue_value->nr_bytes > size) {
    size = issue_value->nr_bytes;
  }
  struct request_trace result = { .insert_ts = insert_value && insert_value->timestamp ? insert_value->timestamp : 0,
                                  .issue_ts = issue_value->timestamp,
                                  .nr_bytes = size,
                                  .complete_ts = ts,
                                  .dev = ctx -> dev,
                                  .sector = ctx->sector,
                                  .common_pid = issue_value->common_pid };
  set_comm(result.comm, issue_value->comm);
  bpf_map_update_elem(&lat_map, &ts, &result, BPF_NOEXIST);

  bpf_map_delete_elem(&insert_ts_map, &key);
  bpf_map_delete_elem(&issue_ts_map, &key);

  return 0;
}

SEC("tp/block/block_rq_insert")
int32_t block_rq_insert(struct block_rq_submission *ctx) {
  trace_start((void *) ctx, 0);

  uint8_t key = BLOCK_RQ_INSERT_KEY;
  struct request_type_statistic *current_value;
  
  current_value = bpf_map_lookup_elem(&trace_map, &key);
  if (!current_value) {
    struct request_type_statistic new_value = {
      .dev = ctx->dev,
      .last_sector = ctx->sector,
      .count = 1,
      .n_bytes = ctx->nr_bytes,
      .n_sectors = ctx->nr_sectors
    };

    bpf_map_update_elem(&trace_map, &key, &new_value, BPF_NOEXIST);
    return 0;
  }

  current_value->count++;
  current_value->n_bytes += ctx->nr_bytes;
  current_value->n_sectors += ctx->nr_sectors;

  return 0;
}

SEC("tp/block/block_rq_issue")
int32_t block_rq_issue(struct block_rq_submission *ctx) {
  trace_start((void *) ctx, 1);

  uint8_t key = BLOCK_RQ_ISSUE_KEY;
  struct request_type_statistic *current_value;
  
  current_value = bpf_map_lookup_elem(&trace_map, &key);
  if (!current_value) {
    struct request_type_statistic new_value = {
      .dev = ctx->dev,
      .last_sector = ctx->sector,
      .count = 1,
      .n_bytes = ctx->nr_bytes,
      .n_sectors = ctx->nr_sectors
    };

    bpf_map_update_elem(&trace_map, &key, &new_value, BPF_NOEXIST);
    return 0;
  }

  current_value->count++;
  current_value->n_bytes += ctx->nr_bytes;
  current_value->n_sectors += ctx->nr_sectors;

  return 0;
}

SEC("tp/block/block_rq_complete")
int32_t block_rq_complete(struct block_rq_complete *ctx) {
  trace_end(ctx);
  uint8_t key = BLOCK_RQ_COMPLETE_KEY;
  struct request_type_statistic *current_value;
  current_value = bpf_map_lookup_elem(&trace_map, &key);

  if (!current_value) {
    struct request_type_statistic new_value = {
      .dev = ctx->dev,
      .last_sector = ctx->sector,
      .count = 1,
      .n_sectors = ctx->nr_sectors,
      .n_errors = 0
    };

    bpf_map_update_elem(&trace_map, &key, &new_value, BPF_NOEXIST);
    return 0;
  }

  current_value->count++;
  current_value->n_sectors += ctx->nr_sectors;
  current_value->n_errors += ctx->error ? 1 : 0;

  return 0;
}

SEC("fentry/add_to_page_cache_lru")
int32_t add_to_page_cache_lru()
{
  uint8_t key = 0;
	uint64_t *current_value = bpf_map_lookup_elem(&cache_misses, &key);
  if (!current_value) {
    uint64_t value = 1;
    bpf_map_update_elem(&cache_misses, &key, &value, BPF_NOEXIST);
    return 0;
  }

  (*current_value)++;

	return 0;
}

SEC("fentry/account_page_dirtied")
int32_t account_page_dirtied()
{
	uint8_t key = 0;
	uint64_t *current_value = bpf_map_lookup_elem(&cache_misses, &key);
  if (!current_value) {
    uint64_t value = 0;
    bpf_map_update_elem(&cache_misses, &key, &value, BPF_NOEXIST);
    return 0;
  }

  (*current_value)--;

	return 0;
}