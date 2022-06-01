/* 
    Keys are structured around the road through the kernel. 
    Block_rq_insert traces when the command is inserted into a subission queue.
    Block_rq_issue traces when the command is issued to the device.
    Block_rq_complete traces when the command is completed from the device.
*/
#define BLOCK_RQ_INSERT_KEY 1
#define BLOCK_RQ_ISSUE_KEY 2
#define BLOCK_RQ_COMPLETE_KEY 3

// Keys for debug counting
#define MISSED_TRACES 1; // For when complete is called with issue.

struct block_rq_submission {
    uint16_t common_type;
    uint8_t common_flags;
    uint8_t common_preempt_count;
    int32_t common_pid;
    uint32_t dev;
    uint64_t sector;
    uint32_t nr_sectors;

    uint32_t nr_bytes;

    int8_t rwbs[8];
    uint8_t comm[16];
    int8_t cmd[4];
};

struct block_rq_complete {
    uint16_t common_type;
    uint8_t common_flags;
    uint8_t common_preempt_count;
    int32_t common_pid;
    uint32_t dev;
    uint64_t sector;
    uint32_t nr_sectors;

    uint32_t error;

    int8_t rwbs[8];
    int8_t cmd[4];
};

struct request_key{
    uint64_t dev;
    uint64_t sector;
};

struct request_value {
    uint64_t timestamp;
    uint64_t nr_bytes;
    int32_t common_pid;
    uint8_t comm[16];
    uint8_t padding[4];
};

struct request_trace {
    uint64_t insert_ts;
    uint64_t issue_ts;
    uint64_t complete_ts;
    uint64_t nr_bytes;

    uint64_t dev;
    uint64_t sector;
	int32_t common_pid;
    uint8_t comm[16];
    uint8_t padding[4];
};

// Stats response.
struct request_type_statistic {
    uint64_t count;
    uint64_t dev;
    uint64_t last_sector;
    uint64_t n_bytes;
    uint64_t n_sectors;
    uint64_t n_errors;
	int64_t common_pid;
};