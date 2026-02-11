from __future__ import annotations


def cpu_busy_query(host_ident: str, primary_ip: str | None = None) -> str:
    labels = [f'ident="{host_ident}"']
    if primary_ip:
        labels.append(f'__primary_ip__="{primary_ip}"')
    label_block = ",".join(labels)
    return f"avg_over_time(cpu_busy{{{label_block}}}[5m])"


def disk_used_percent_query(host_ident: str, mountpoint: str = "/") -> str:
    return (
        "100 * (1 - "
        f"node_filesystem_avail_bytes{{instance=\"{host_ident}\",mountpoint=\"{mountpoint}\",fstype!~\"tmpfs|overlay\"}}"
        " / "
        f"node_filesystem_size_bytes{{instance=\"{host_ident}\",mountpoint=\"{mountpoint}\",fstype!~\"tmpfs|overlay\"}}"
        ")"
    )
