from pathlib import Path
from math import ceil


def generate_architecture_devices(
    floors,
    rooms_per_floor,
    users_per_room,
    width,
    unit,
    building_type,
    output_dir
):
    devices = []

    # -----------------------------
    # CORE LAYER (always present)
    # -----------------------------
    devices.append("core_router_1")
    devices.append("dhcp_server")
    devices.append("dns_server")
    devices.append("internet_cloud")

    bt = building_type.strip().lower()

    # End-device type
    # office/school/hospital => PCs, hotel => laptops
    end_prefix = "laptop" if bt == "hotel" else "pc"

    # -----------------------------
    # FLOOR BASED GENERATION
    # -----------------------------
    for f in range(1, floors + 1):

        # Distribution switch per floor
        devices.append(f"dist_switch_f{f}")

        # Access switch per room + end devices per room
        for r in range(1, rooms_per_floor + 1):
            devices.append(f"access_switch_f{f}_r{r}")

            # Add end devices with floor+room naming
            for u in range(1, users_per_room + 1):
                devices.append(f"{end_prefix}_f{f}_r{r}_u{u}")

        # -----------------------------
        # Access Points rule
        # -----------------------------
        # 1 AP per 10 users (per floor)
        users_on_floor = rooms_per_floor * users_per_room
        ap_count = max(1, ceil(users_on_floor / 10))

        for ap in range(1, ap_count + 1):
            devices.append(f"ap_f{f}_{ap}")

    # -----------------------------
    # BUILDING TYPE RULES
    # -----------------------------
    if bt == "hospital":
        devices.append("medical_server")
    elif bt in ("school / university", "school/university"):
        devices.append("campus_server")
    elif bt == "office":
        devices.append("office_server")
    elif bt == "hotel":
        devices.append("guest_portal_server")

    # -----------------------------
    # WRITE TXT
    # -----------------------------
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "architecture_devices.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        for d in devices:
            f.write(d + "\n")

    return str(file_path)