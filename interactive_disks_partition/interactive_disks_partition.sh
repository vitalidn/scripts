#!/usr/bin/env bash
set -euo pipefail

HOST=""
SUDO_PASSWORD=""
LOG_FILE="/tmp/disk_partition.log"
HOSTS=()

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { 
    echo -e "${GREEN}INFO:${NC} $*" | tee -a >(echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $*" >> "$LOG_FILE")
}

log_warn() { 
    echo -e "${YELLOW}WARNING:${NC} $*" | tee -a >(echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $*" >> "$LOG_FILE")
}

log_error() { 
    echo -e "${RED}ERROR:${NC} $*" | tee -a >(echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >> "$LOG_FILE")
    exit 1
}

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_warn "Script terminated with error code $exit_code"
    fi
    [[ -f "/tmp/partition_backup.bin" && $exit_code -eq 0 ]] && rm -f "/tmp/partition_backup.bin" && log_info "Cleanup done"
    SUDO_PASSWORD=""
    exit $exit_code
}
trap cleanup EXIT INT TERM

# Function to format size in human readable format
format_size() {
    local size=$1
    # Convert to GiB
    size=$((size/1024/1024/1024))
    echo "${size}GiB"
}

run_cmd() {
    local cmd="$*"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Executing: sudo $cmd" >> "$LOG_FILE"
    ssh -tt "$HOST" "echo '$SUDO_PASSWORD' | sudo -S bash -c '$cmd' 2>/dev/null" 2>/dev/null || log_error "Command failed: $cmd"
}

check_ssh_and_sudo() {
    local host="$1"
    log_info "Checking SSH and sudo access..."
    
    if ! ssh -q -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "$host" exit 2>/dev/null; then
        # If SSH fails, try ping
        if ! ping -c 1 -W 5 "$host" >/dev/null 2>&1; then
            log_error "SSH connection failed. You may not have received authorization for network access in Lynx"
        else
            log_error "Network access is available but SSH access to the host is not possible"
        fi
    fi
    
    # Only ask for password if it's not already set
    if [[ -z "$SUDO_PASSWORD" ]]; then
        read -sp "Enter sudo password: " SUDO_PASSWORD
        echo
    fi
    
    ssh -tt "$host" "echo '$SUDO_PASSWORD' | sudo -S true 2>/dev/null" 2>/dev/null || log_error "Sudo access failed"
    ssh -tt "$host" "echo '$SUDO_PASSWORD' | sudo -S bash -c 'sudo -v' 2>/dev/null" 2>/dev/null
    log_info "Access OK"
}

get_available_disks() {
    echo -e "\n${YELLOW}Available disks:${NC}"
    echo "----------------------------------"
    if ! run_cmd "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -v 'loop' | grep -v 'sr'"; then
        log_error "Failed to get disk information"
    fi
    echo "----------------------------------"
}

check_disk_space() {
    local disk="$1"
    local required_size="$2"
    local available_size
    available_size=$(get_disk_size_gib "$disk")
    
    if (( required_size > available_size )); then
        log_error "$disk: not enough space (need $(format_size $((required_size*1024*1024*1024))), have $(format_size $((available_size*1024*1024*1024))))"
    fi
    log_info "$disk: available space $(format_size $((available_size*1024*1024*1024)))"
}

validate_disk() {
    local disk="$1"
    [[ "$disk" != /dev/* ]] && disk="/dev/$disk"
    run_cmd "test -b \"$disk\""
}

get_disk_size_gib() {
    local disk="$1"
    [[ "$disk" != /dev/* ]] && disk="/dev/$disk"
    run_cmd "lsblk -b -d -n -o SIZE $disk" | awk '{printf "%.0f", $1/1024/1024/1024}'
}

prevent_system_disk_modification() {
    local disk="$1"
    if [[ "$disk" == "/dev/sda" ]]; then
        read -rp "WARNING: $disk may be a system disk. Continue? (y/N): " confirm
        [[ "$confirm" != "y" ]] && log_info "User aborted" && exit 1
    fi
}

validate_partition_count() {
    [[ "$1" =~ ^[0-9]+$ ]] && (( $1 >= 1 && $1 <= 128 ))
}

validate_partition_size() {
    [[ "$1" =~ ^[0-9]+$ ]] && (( $1 >= 1 && $1 <= 1000000 ))
}

check_existing_partitions() {
    local disk="$1"
    [[ "$disk" != /dev/* ]] && disk="/dev/$disk"
    
    local partitions
    partitions=$(run_cmd "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT $disk" | grep 'part' || true)
    
    if [[ -n "$partitions" ]]; then
        echo -e "\n${YELLOW}WARNING: Disk $disk already has partitions:${NC}"
        echo "----------------------------------------------------------------"
        echo "$partitions"
        echo "----------------------------------------------------------------"
        
        read -rp "Do you want to proceed with new partitioning? This will delete all existing partitions! (y/N): " confirm
        if [[ "$confirm" != "y" ]]; then
            log_info "Operation canceled by user for disk $disk"
            echo -e "${YELLOW}Skipping disk $disk. You can continue with other disks.${NC}"
            return 1
        fi
    else
        log_info "Disk $disk is unpartitioned..."
        local disk_size
        disk_size=$(run_cmd "lsblk -b -d -n -o SIZE $disk" | awk '{printf "%.0f", $1/1024/1024/1024}')
        log_info "Disk size: ${disk_size}GiB"
    fi
    return 0
}

create_partition() {
    local disk="$1"
    local index="$2"
    local size="$3"
    log_info "Creating partition $index on $disk (${size}GiB)"
    run_cmd "sgdisk --new=$index:0:+${size}G --typecode=$index:8300 --change-name=$index:data$index $disk >/dev/null 2>&1"
}

verify_partitions() {
    local disk="$1"
    local expected_count="$2"
    local actual_count
    actual_count=$(run_cmd "gdisk -l $disk" | grep -c '^[[:space:]]*[0-9]')
    [[ "$actual_count" -ne "$expected_count" ]] && log_error "Mismatch on $disk: expected $expected_count, got $actual_count"
    log_info "Verified partitions on $disk"
}

parse_host_range() {
    local input="$1"
    local prefix suffix start end
    
    # Check if input contains a range
    if [[ "$input" =~ ^(.*)\[([0-9]+):([0-9]+)\](.*)$ ]]; then
        prefix="${BASH_REMATCH[1]}"
        start="${BASH_REMATCH[2]}"
        end="${BASH_REMATCH[3]}"
        suffix="${BASH_REMATCH[4]}"
        
        # Validate range
        if (( start > end )); then
            log_error "Invalid range: start ($start) is greater than end ($end)"
        fi
        
        # Generate host list
        for i in $(seq "$start" "$end"); do
            HOSTS+=("$prefix$i$suffix")
        done
    else
        # Single host
        HOSTS+=("$input")
    fi
}

execute_on_host() {
    local host="$1"
    local current_user
    current_user=$(whoami)
    HOST="$current_user@$host"
    
    local hostname
    hostname=$(echo "$HOST" | cut -d@ -f2)
    LOG_FILE="./${hostname}.log"
    touch "$LOG_FILE"
    log_info "Starting disk partitioning for host: $hostname"
    
    check_ssh_and_sudo "$HOST"
    get_available_disks

    while true; do
        read -rp "Enter disks to partition (space-separated, e.g. sda sdb) or 'N' to skip this host: " TARGET_DISKS
        if [[ "$TARGET_DISKS" =~ ^[Nn]$ ]]; then
            log_info "Skipping host $hostname as requested"
            return 0
        fi
        [[ -z "$TARGET_DISKS" ]] && echo "Please enter disk names or 'N' to skip" && continue
        break
    done

    IFS=' ' read -r -a DISK_ARRAY <<< "$TARGET_DISKS"

    local -a PROCESSED_DISKS=()

    for disk in "${DISK_ARRAY[@]}"; do
        if validate_disk "$disk"; then
            if check_existing_partitions "$disk"; then
                prevent_system_disk_modification "$disk"
                PROCESSED_DISKS+=("$disk")
            fi
        else
            log_error "Disk $disk is not valid"
        fi
    done

    if [[ ${#PROCESSED_DISKS[@]} -eq 0 ]]; then
        log_info "No disks were approved for partitioning. Skipping host $hostname."
        return 0
    fi

    DISK_ARRAY=("${PROCESSED_DISKS[@]}")

    while true; do
        read -rp "Enter number of partitions per disk (1-128): " COUNT_FIXED
        validate_partition_count "$COUNT_FIXED" && break || echo "Invalid number (must be between 1 and 128)"
    done

    while true; do
        read -rp "Enter partition size in GiB: " PART_GIB
        validate_partition_size "$PART_GIB" && break || echo "Invalid size"
    done

    REQUIRED_SIZE_GIB=$((COUNT_FIXED * PART_GIB))
  
    echo -e "\n${YELLOW}Partitioning Summary:${NC}"
    echo "----------------------------------------------"
    echo "Host: $hostname"
    echo "Disks to partition: ${DISK_ARRAY[*]}"
    echo "Partitions per disk: $COUNT_FIXED"
    echo "Partition size: ${PART_GIB}GiB"
    echo "Total required per disk: ${REQUIRED_SIZE_GIB}GiB"
    echo -e "${YELLOW}Note:${NC} An additional partition will be created using the remaining space on each disk"
    echo "-----------------------------------------------"

    read -rp "Proceed with partitioning? (y/N): " confirm
    [[ "$confirm" != "y" ]] && log_info "Operation canceled by user" && return

    for disk in "${DISK_ARRAY[@]}"; do
        [[ "$disk" != /dev/* ]] && disk="/dev/$disk"
        log_info "Starting partitioning process for $disk..."

        log_info "Creating backup of partition table..."
        run_cmd "sgdisk -b /tmp/partition_backup.bin $disk >/dev/null 2>&1"

        log_info "Clearing disk and creating GPT..."
        run_cmd "sgdisk --zap-all $disk >/dev/null 2>&1"
        run_cmd "sgdisk --mbrtogpt $disk >/dev/null 2>&1"

        log_info "Creating fixed-size partitions..."
        for i in $(seq 1 "$COUNT_FIXED"); do
            create_partition "$disk" "$i" "$PART_GIB"
        done
        log_info "Creating remaining space partition..."
        run_cmd "sgdisk --largest-new=0 --typecode=0:8300 --change-name=0:data$((COUNT_FIXED + 1)) $disk >/dev/null 2>&1"

        verify_partitions "$disk" "$((COUNT_FIXED + 1))"
        log_info "Partitioning completed for $disk"
    done

    echo -e "\n${YELLOW}Final partition layout for disk(s) ${NC}"
    echo -e "${YELLOW}$hostname${NC}"
    echo -e "${YELLOW}----------------------------------------------${NC}"
    run_cmd "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -v 'loop'"
    run_cmd "ls -l /dev/disk/by-id | grep -v 'sdc' |  awk '{print \$9,\$10,\$11}'"
    echo -e "\n${GREEN}--------------------------------------------------${NC}"
    log_info "All disk(s) partitioned successfully!!!"
    echo -e "${GREEN}--------------------------------------------------${NC}"
}

main() {
    # Initialize log file
    touch "$LOG_FILE"
    
    # Check if host was provided as argument
    if [[ $# -ge 1 ]]; then
        HOST_INPUT="$1"
        # If password was provided as second argument
        if [[ $# -ge 2 ]]; then
            SUDO_PASSWORD="$2"
        fi
    else
        while true; do
            read -rp "Enter Host (format prefix-[start:end].suffix or prefix-[num].suffix): " HOST_INPUT
            [[ -z "$HOST_INPUT" ]] && echo "Host cannot be empty" && continue
            break
        done
    fi

    parse_host_range "$HOST_INPUT"
    log_info "Processing ${#HOSTS[@]} host(s)"
    
    for host in "${HOSTS[@]}"; do
        echo -e "\n${YELLOW}Processing host: $host${NC}"
        execute_on_host "$host"
    done
    log_info "All hosts processed"
}

main "$@"