"""Coordinate and packed-byte layout arithmetic for the Rev4 scanout path."""
from math import ceil

PHYSICAL_WIDTH = 480
PHYSICAL_HEIGHT = 800
CANVAS_OFFSET = 40
CODED_WIDTH = 720
CODED_HEIGHT = 480


def coded_to_physical(u, v):
    """Coded x=u/y=v -> LCD active physical x/y, from core address RTL."""
    if not (0 <= u < CODED_WIDTH and 0 <= v < CODED_HEIGHT):
        raise ValueError('coded coordinate outside 720x480')
    return v, u + CANVAS_OFFSET


def physical_to_coded(px, py):
    """Return coded x/y inside canvas; None for the 40-pixel top/bottom bars."""
    if not (0 <= px < PHYSICAL_WIDTH and 0 <= py < PHYSICAL_HEIGHT):
        raise ValueError('physical coordinate outside 480x800')
    if py < CANVAS_OFFSET or py >= CANVAS_OFFSET + CODED_WIDTH:
        return None
    return py - CANVAS_OFFSET, px


def portrait_word_address(u, v, base=0):
    """Existing core's RGB565 word address: base+(x+40)*480+y."""
    px, py = coded_to_physical(u, v)
    assert px == v and py == u + CANVAS_OFFSET
    return base + py * PHYSICAL_WIDTH + px


def storage_index(layout, u, v, width, height):
    """Byte/sample index; u is coded-width axis, v is coded-height axis."""
    if not (0 <= u < width and 0 <= v < height):
        raise ValueError('plane coordinate out of bounds')
    if layout == 'canonical_row_major':
        return v * width + u
    if layout == 'plane_transposed':
        return u * height + v
    if layout == 'tile_major_coded':
        return ((v // 8) * (width // 8) + (u // 8)) * 64 + (v % 8) * 8 + (u % 8)
    if layout == 'tile_major_physical_scan':
        return ((u // 8) * (height // 8) + (v // 8)) * 64 + (u % 8) * 8 + (v % 8)
    raise ValueError(f'unknown layout: {layout}')


def coded_block_order(width, height):
    """Block-row-major 8x8 transform output order in conventional (v,u) grid."""
    if width % 8 or height % 8:
        raise ValueError('plane geometry must align to 8x8 blocks')
    for tv in range(height // 8):
        for tu in range(width // 8):
            for lv in range(8):
                for lu in range(8):
                    yield tu * 8 + lu, tv * 8 + lv


def physical_scan_order(width, height):
    """One unique sample pass in portrait active-raster order (physical y,x)."""
    for u in range(width):
        for v in range(height):
            yield u, v


def trace_metrics(indices, sample_count, burst_bytes=16):
    """Count contiguous +1 runs and aligned bursts per run, with no cache reuse."""
    runs = 0
    bursts = 0
    run_start = run_end = previous = None
    seen = 0

    def finish(start, end):
        return end // burst_bytes - start // burst_bytes + 1

    for addr in indices:
        if addr < 0 or addr >= sample_count:
            raise ValueError('address outside packed plane')
        seen += 1
        if run_start is None:
            run_start = run_end = previous = addr
            runs = 1
        elif addr == previous + 1:
            run_end = previous = addr
        else:
            bursts += finish(run_start, run_end)
            runs += 1
            run_start = run_end = previous = addr
    if run_start is not None:
        bursts += finish(run_start, run_end)
    if seen != sample_count:
        raise ValueError(f'trace covered {seen}, expected {sample_count} samples')
    useful = sample_count
    capacity = bursts * burst_bytes
    return {
        'samples': seen,
        'contiguous_runs': runs,
        'aligned_16B_bursts_without_cross_run_cache': bursts,
        'logical_bytes': useful,
        'burst_capacity_bytes': capacity,
        'burst_utilization': useful / capacity if capacity else 1.0,
    }
