PLATFORM_ID = $$( uname -s )
PLATFORM = $$( \
	case $(PLATFORM_ID) in \
		( Linux | FreeBSD | OpenBSD | NetBSD ) echo $(PLATFORM_ID) ;; \
		( * ) echo Unrecognized ;; \
	esac)

CTAGS = $$( \
	case $(PLATFORM_ID) in \
		( Linux ) echo "ctags" ;; \
		( FreeBSD | OpenBSD | NetBSD ) echo "exctags" ;; \
		( * ) echo Unrecognized ;; \
	esac)

MAKE = $$( \
	case $(PLATFORM_ID) in \
		( Linux ) echo "make" ;; \
		( FreeBSD | OpenBSD | NetBSD ) echo "gmake" ;; \
		( * ) echo Unrecognized ;; \
	esac)

NPROC = $$( \
	case $(PLATFORM_ID) in \
		( Linux ) nproc ;; \
		( FreeBSD | OpenBSD | NetBSD ) sysctl -n hw.ncpu ;; \
		( * ) echo Unrecognized ;; \
	esac)

PTARGET = $$( \
	case $(PLATFORM_ID) in \
		( Linux ) echo "linux" ;; \
		( FreeBSD | OpenBSD | NetBSD ) echo "freebsd" ;; \
		( * ) echo Unrecognized ;; \
	esac)

BUILD_DIR?=build

.PHONY: default
default: all

.PHONY: ebpf
ebpf: 
	@echo "## meta: make ebpf"
	@if [ ! -d "$(BUILD_DIR)/ebpf" ]; then	\
		mkdir -p "$(BUILD_DIR)/ebpf";	\
	fi
	cd ebpf && ${MAKE} all

.PHONY: all
all: deps ebpf

.PHONY: clean
clean:
	@echo "## meta: make clean"
	rm -fr $(BUILD_DIR) || true

.PHONY: deps
deps: deps-fetch rocks-static fio-install libbpf-install

.PHONY: deps-fetch
deps-fetch:	rocks-fetch fio-fetch libbpf-fetch python-deps

.PHONY: deps-clean
deps-clean:	rocks-clean fio-clean libbpf-clean

.PHONY: python-deps
python-deps: 
	@echo "pip3 install"
	sudo pip3 install matplotlib pandas

### RocksDB
.PHONY: rocks-static
rocks-static:
	@echo "## RocksDB: make static_lib"
	cd third-party/rocksdb && ${MAKE} -j $(NPROC) static_lib

.PHONY: rocks-clean
rocks-clean:
	@echo "## RocksDB: make clean"
	cd third-party/rocksdb && ${MAKE} clean

.PHONY: rocks-fetch
rocks-fetch:
	@echo "## Updating RocksDB repo"
	@git submodule update --init
	cd third-party/rocksdb && git fetch && git checkout v7.1.2

### FIO
.PHONY: fio-install
fio-install:
	@echo "## FIO: make install"
	cd third-party/fio && ./configure && ${MAKE} -j $(NPROC) && sudo ${MAKE} install

.PHONY: fio-clean
fio-clean:
	@echo "## FIO: make clean"
	cd third-party/fio && ${MAKE} clean

.PHONY: fio-fetch
fio-fetch:
	@echo "## Updating FIO repo"
	@git submodule update --init
	cd third-party/fio && git fetch && git checkout fio-3.28

### Libbpf
.PHONY: libbpf-install
libbpf-install:
	@echo "## libbpf: make install"
	$(MAKE) --directory=third-party/libbpf/src all
	DESTDIR=root $(MAKE) -j $(NPROC) --directory=third-party/libbpf/src install_headers

.PHONY: libbpf-clean
libbpf-clean:
	@echo "## libbpf: make clean"
	$(MAKE) --directory=third-party/libbpf/src clean

.PHONY: libbpf-fetch
libbpf-fetch:
	@echo "## Updating libbpf repo"
	@git submodule update --init
	cd third-party/libbpf && git fetch && git checkout 94a4985
