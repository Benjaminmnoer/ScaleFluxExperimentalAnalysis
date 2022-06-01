#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <libgen.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "tracing.h"

void print_results(struct request_type_statistic results, char title[], FILE *fptr){
  fprintf(fptr, "------ %s ------\n", title);
  fprintf(fptr, "Count: %lu\n", results.count);
  fprintf(fptr, "Latest device identifier: %lu\n", results.dev);
  fprintf(fptr, "Latest sector: %lu\n", results.last_sector);
  fprintf(fptr, "Number of sectors: %lu\n", results.n_sectors);
  fprintf(fptr, "Number of bytes: %lu\n", results.n_bytes);
  fprintf(fptr, "%lu errors registered!\n", results.n_errors);
}

void print_debug(struct bpf_object *obj){
  uint16_t key;
  uint16_t has_result;
  uint64_t result;
  printf("------ DEBUG ------\n");
  struct bpf_map *debug_map = bpf_object__find_map_by_name(obj, "debug_map");
  int32_t debug_map_fd = bpf_map__fd(debug_map);
  key = MISSED_TRACES;
  has_result = bpf_map_lookup_elem(debug_map_fd, &key, &result);
  if (has_result){
    printf("Missed traces: %lu\n", result);
  }
}

int main(int argc, char **argv) {
  if (argc < 3){
    printf("Unexpected invocation. Expected call like\n./ebpf_ssd_analysis [COMMAND] [output_base]");
    return -1;
  }

  char path[PATH_MAX];
  sprintf(path, "%s/kernel.o", dirname(argv[0]));
  char command[1000];
  sprintf(command, "%s", argv[1]);
  char output_base[PATH_MAX];
  sprintf(output_base, "%s", argv[2]);

  struct request_type_statistic results;
  struct bpf_object *obj;
  int8_t key;
  int32_t prog_fd;
  int32_t has_result = 0;

  if (bpf_prog_load(path, BPF_PROG_TYPE_TRACEPOINT, &obj, &prog_fd) != 0) {
    printf("The kernel didn't load the BPF program\n");
    return -1;
  }

  if (prog_fd < 1) {
    printf("Error creating prog_fd\n");
    return -2;
  }

  struct bpf_program *prog;
  prog = bpf_object__find_program_by_name(obj, "block_rq_issue");
  bpf_program__attach(prog);
  prog = bpf_object__find_program_by_name(obj, "block_rq_insert");
  bpf_program__attach(prog);
  prog = bpf_object__find_program_by_name(obj, "block_rq_complete");
  bpf_program__attach(prog);

  printf("eBPF will listen to I/O!\n");
  // sleep(610);

  system(command);

  print_debug(obj);
  char statsfile[PATH_MAX];
  sprintf(statsfile, "%s_stats.log", output_base);
  FILE *stats_ptr = fopen(statsfile, "w");

  struct bpf_map *trace_map = bpf_object__find_map_by_name(obj, "trace_map");
  int64_t trace_map_fd = bpf_map__fd(trace_map);

  // Iterate over all keys in the map
  key = BLOCK_RQ_INSERT_KEY;
  has_result = bpf_map_lookup_elem(trace_map_fd, &key, &results);
  if (!has_result) {
    print_results(results, "Block_rq_insert results", stats_ptr);
  }

  key = BLOCK_RQ_ISSUE_KEY;
  has_result = bpf_map_lookup_elem(trace_map_fd, &key, &results);
  if (!has_result) {
    print_results(results, "Block_rq_issue results", stats_ptr);
  }

  key = BLOCK_RQ_COMPLETE_KEY;
  has_result = bpf_map_lookup_elem(trace_map_fd, &key, &results);
  if (!has_result) {
    print_results(results, "Block_rq_complete results", stats_ptr);
  }

  // struct bpf_map *cache_map = bpf_object__find_map_by_name(obj, "cache_misses");
  // int64_t cache_map_fd = bpf_map__fd(cache_map);
  // key = 0;
  // uint64_t result = 0;
  // has_result = bpf_map_lookup_elem(cache_map_fd, &key, &result);
  // if (!has_result) {
  //   fprintf(stats_ptr, "Cache misses: %lu\n", result);
  // }

  fclose(stats_ptr);

  char timelinefile[PATH_MAX];
  sprintf(timelinefile, "%s_timeline.log", output_base);
  FILE *timeline_ptr = fopen(timelinefile, "w");

  fprintf(timeline_ptr, "------ Timestamps ------\n");
  struct bpf_map *lat_map = bpf_object__find_map_by_name(obj, "lat_map");
  int32_t lat_map_fd = bpf_map__fd(lat_map);
  uint64_t prev_key;
  uint64_t req_key;
  int32_t has_value = 0;
  struct request_trace trace;
  fprintf(timeline_ptr, "Insert, issue, complete, size, comm");
  while (bpf_map_get_next_key(lat_map_fd, &prev_key, &req_key) == 0) {
    has_value = bpf_map_lookup_elem(lat_map_fd, &req_key, &trace);
    if (has_value >= 0){
      // Insert issue complete  size  comm
      fprintf(timeline_ptr, "%lu, %lu, %lu, %lu, %s\n", \
                            trace.insert_ts, trace.issue_ts, trace.complete_ts, trace.nr_bytes, trace.comm);
    }
    prev_key = req_key;
    has_value = -1;
  }

  fclose(timeline_ptr);
  return 0;
}