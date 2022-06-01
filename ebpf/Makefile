TARGET := ebpf-ssd-analysis

SRC_DIR = $(shell realpath .)
LIBBPF_DIR = $(SRC_DIR)/../third-party/libbpf/src/
CFLAGS ?= -I$(LIBBPF_DIR)/root/usr/include/ -g
LDFLAGS ?= -L$(LIBBPF_DIR)

LIBS = -lbpf -lelf

BUILD_DIR?=../build/ebpf

all: $(TARGET) kernel

vmlinux: 
	bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

$(TARGET): %: user.c Makefile
	gcc $(CFLAGS) $(LDFLAGS) -o $(BUILD_DIR)/$(TARGET) user.c -Wl,-rpath=$(LIBBPF_DIR) $(LIBS)

kernel: kernel.c
	clang -S \
	    -target bpf \
	    -D __BPF_TRACING__ \
	    $(CFLAGS) \
	    -Wall \
	    -Werror \
	    -O2 -emit-llvm -c -g --output=$(BUILD_DIR)/kernel.ll kernel.c
	llc -march=bpf -filetype=obj -o $(BUILD_DIR)/kernel.o $(BUILD_DIR)/kernel.ll