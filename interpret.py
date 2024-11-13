from __future__ import annotations
from PIL import Image
import os
import sys
from dataclasses import dataclass
import math

sys.setrecursionlimit(1000000)

program_file = "programs/sierpinski.png"
output_file = "output.png"
if len(sys.argv) > 1:
    program_file = sys.argv[1]
if len(sys.argv) > 2:
    output_file = sys.argv[2]

library_folder = "images"
library = []
base_grid = 5

# recursively load all library images
# ensure all images are the same size (base_grid x base_grid)
# store name (including subfolders) and image in library

black = (0, 0, 0, 255)
white = (255, 255, 255, 255)
red = (255, 0, 0, 255)
orange = (255, 165, 0, 255)
lightblue = (173, 216, 230, 255)
def isblack(x):
    # return x == black
    diff = sum(abs(a-b) for a,b in zip(x, black))
    return diff < 10

for root, dirs, files in os.walk(library_folder):
    for file in files:
        if file.endswith(".png"):
            img = Image.open(os.path.join(root, file))
            if img.size != (base_grid, base_grid):
                print("Error: image", file, "is not", base_grid, "x", base_grid)
                continue
            # subfolder but not library folder
            filename = os.path.join(root, file)
            filename = filename.removeprefix(library_folder + "/")
            filename = filename.removesuffix(".png")
            # convert to boolean array
            data = img.getdata()
            # use alpha key
            data = [1 if isblack(x) else 0 for x in data]
            library.append((filename, data))
            
img = Image.open(program_file)
w,h = img.size
assert w % base_grid == 0
assert h % base_grid == 0

empty_tile = "empty"
# convert to array of tiles
data = img.getdata()
tiles = []
tile_data = []
for y in range(0, h, base_grid):
    row = []
    data_row = []
    for x in range(0, w, base_grid): 
        tile = [
            [data[ty*w + tx] for tx in range(x, x+base_grid)] 
            for ty in range(y, y+base_grid)
        ]
        tile = [1 if isblack(x) else 0 for row in tile for x in row]
        # find matching tile in library
        found = None
        for name, lib_tile in library:
            if lib_tile == tile:
                found = name
                break
        if found is None:
            found = empty_tile
        row.append(found)
        data_row.append(tile)
    tiles.append(row)
    tile_data.append(data_row)
    
def position(x,y):
    return f"{x}, {y} ({x*base_grid}, {y*base_grid})"


@dataclass
class Canvas:
    position: tuple[int, int] | None
    size: tuple[int, int]
    data: list[list[int]] 
    
    def set(self, x, y, value):
        new_data = [[v for v in row] for row in self.data]
        new_data[y][x] = value
        return Canvas(None, self.size, new_data)
        
    
def get_canvas(x, y):
    if tiles[y][x] != "canvas":
        return None
    max_x = x+1
    # top side
    while tiles[y][max_x] == "wire_we":
        max_x += 1
    # top right corner
    if tiles[y][max_x] != "wire_sw":
        return None
    max_y = y+1
    # left side
    while tiles[max_y][x] == "wire_ns":
        max_y += 1
    # bottom left corner
    if tiles[max_y][x] != "wire_ne":
        return None
    # check bottom side
    for tx in range(x+1, max_x):
        if tiles[max_y][tx] != "wire_we":
            return None
    # check right side
    for ty in range(y+1, max_y):
        if tiles[ty][max_x] != "wire_ns":
            return None
    # bottom right corner
    if tiles[max_y][max_x] != "wire_nw":
        return None
    
    content = []
    for ty in range(y+1, max_y):
        row = []
        for tx in range(x+1, max_x):
            row.append(tile_data[ty][tx])
        content.append(row)
    # flatten content
    # ch * cw * base_grid * base_grid -> (ch * base_grid) * (cw * base_grid)
    
    # Initialize the flattened `raw_content` array
    ch = max_y - (y + 1)
    cw = max_x - (x + 1)
    dw = cw * base_grid
    dh = ch * base_grid
    raw_content = [[0] * dw for _ in range(dh)]

    # Fill `raw_content` with the flattened data from `content`
    for ty in range(ch):
        for tx in range(cw):
            # `tile` is the `base_grid * base_grid` array at `content[ty][tx]`
            tile = content[ty][tx]
            for i in range(base_grid):
                for j in range(base_grid):
                    # Map each element of `tile` to the appropriate place in `raw_content`
                    raw_content[ty * base_grid + i][tx * base_grid + j] = tile[i * base_grid + j]
        
    
    return Canvas((x, y), (dw,dh), raw_content)

number_tiles = {
    "functions/dot": ".",
    "functions/sub": "-",
} | {f"functions/{i}": str(i) for i in range(10)}

def get_number(x, y):
    s = ""
    while tiles[y][x] in number_tiles:
        s += number_tiles[tiles[y][x]]
        x += 1
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None
        
def get_slider_value(x, y):
    l_pos = x
    m_pos = None
    px = x+1
    while tiles[y][px] == "functions/slider_m" or tiles[y][px] == "wire_we":
        if tiles[y][px] == "functions/slider_m":
            m_pos = px
        px += 1
    if m_pos is None:
        print(f"Error: no middle slider found at {position(x,y)}", file=sys.stderr)
        print(f"Ending at {px} with {tiles[y][px]}")
        return None
    if tiles[y][px] != "functions/slider_r":
        print(f"Error: no right slider found at {position(x,y)}", file=sys.stderr)
        return None
    r_pos = px
    l_value = get_number(l_pos, y-1)
    r_value = get_number(r_pos, y-1)
    if l_value is None:
        print(f"Error: no left value found at {position(l_pos,y-1)}", file=sys.stderr)
        return None
    if r_value is None:
        print(f"Error: no right value found at {position(r_pos,y-1)}", file=sys.stderr)
        return None
    alpha = (m_pos - (l_pos+1)) / ((r_pos-1) - (l_pos+1))
    v = l_value + alpha * (r_value - l_value)
    return v
        
def get_value(x, y, direction, mapping):
    if (x, y) in mapping:
        return mapping[(x, y)]
    
    tile = tiles[y][x]
    if tile == "canvas":
        return get_canvas(x, y)
    if tile == "end_e":
        if direction == "w":
            return None
        else:
            return get_value(x+1, y, "e", mapping)
    if tile == "end_s":
        if direction == "n":
            return None
        else:
            return get_value(x, y+1, "s", mapping)
    
    # wire traversal
    if tile == "wire_ne" and direction == "w":
        # if we entered into west (from right), we go up (north)
        return get_value(x, y-1, "n", mapping)
    if tile == "wire_ne" and direction == "s":
        return get_value(x+1, y, "e", mapping)
    if tile == "wire_ns" and direction == "n":
        return get_value(x, y-1, "n", mapping)
    if tile == "wire_ns" and direction == "s":
        return get_value(x, y+1, "s", mapping)
    if tile == "wire_nw" and direction == "e":
        return get_value(x, y-1, "n", mapping)
    if tile == "wire_nw" and direction == "s":
        return get_value(x-1, y, "w", mapping)
    if tile == "wire_se" and direction == "n":
        return get_value(x+1, y, "e", mapping)
    if tile == "wire_se" and direction == "w":
        return get_value(x, y+1, "s", mapping)
    if tile == "wire_sw" and direction == "e":
        return get_value(x, y+1, "s", mapping)
    if tile == "wire_sw" and direction == "n":
        return get_value(x-1, y, "w", mapping)
    if tile == "wire_we" and direction == "e":
        return get_value(x+1, y, "e", mapping)
    if tile == "wire_we" and direction == "w":
        return get_value(x-1, y, "w", mapping)
    # bridge
    if tile == "bridge" and direction == "n":
        return get_value(x, y-1, "n", mapping)
    if tile == "bridge" and direction == "s":
        return get_value(x, y+1, "s", mapping)
    if tile == "bridge" and direction == "e":
        return get_value(x+1, y, "e", mapping)
    if tile == "bridge" and direction == "w":
        return get_value(x-1, y, "w", mapping)
    # joins
    if tile == "join_nse" and (direction == "n" or direction == "w"):
        return get_value(x, y-1, "n", mapping)
    if tile == "join_nsw" and (direction == "n" or direction == "e"):
        return get_value(x, y-1, "n", mapping)
    if tile == "join_nwe" and (direction == "e" or direction == "w"):
        return get_value(x, y-1, "n", mapping)
        
    # app
    if tile == "app" and direction == "w":
        f = get_value(x, y+1, "s", mapping)
        arg = get_value(x, y-1, "n", mapping)
        if f is None:
            print(f"Error: function not found at {position(x,y)}", file=sys.stderr)
            return None
        if arg is None:
            print(f"Error: argument not found at {position(x,y)}", file=sys.stderr)
            return None
        return f(arg)
    # lambda
    if tile == "lambda":
        local_x = x
        local_y = y
        
        def f(arg):
            return get_value(local_x+2, local_y, "none", mapping | {(local_x+1,local_y): arg} | {(local_x,local_y): f})
        return f
    # entry
    if tile == "functions/entry":
        content = get_value(x+1, y, "none", mapping)
        ret = get_value(x+2, y, "none", mapping)
        return content, ret
        
    # slider
    if tile == "functions/slider_l":
        return get_slider_value(x, y)
    
    # functions
    for nt in number_tiles:
        if tile == nt:
            n = get_number(x, y)
            if n is not None:
                return n
    # arithmetic
    if tile == "functions/add":
        return lambda x: lambda y: x+y
    if tile == "functions/mul":
        return lambda x: lambda y: x*y
    if tile == "functions/div":
        return lambda x: lambda y: \
            x / y if isinstance(x, float) or isinstance(y, float) else x // y
    if tile == "functions/sub":
        return lambda x: lambda y: x - y
    if tile == "functions/mod":
        return lambda x: lambda y: x % y
    if tile == "functions/pow":
        return lambda x: lambda y: x ** y
    if tile == "functions/floor":
        return lambda x: int(x)
    if tile == "functions/equal":
        return lambda x: lambda y: x == y
    if tile == "functions/unequal":
        return lambda x: lambda y: x != y
    if tile == "functions/greater":
        return lambda x: lambda y: x > y
    if tile == "functions/less":
        return lambda x: lambda y: x < y
    if tile == "functions/greater_equal":
        return lambda x: lambda y: x >= y
    if tile == "functions/less_equal":
        return lambda x: lambda y: x <= y
    if tile == "functions/and":
        return lambda x: lambda y: x and y
    if tile == "functions/or":
        return lambda x: lambda y: x or y
    if tile == "functions/not":
        return lambda x: not x
    if tile == "functions/if":
        return lambda cond: lambda then_branch: lambda else_branch: then_branch(()) if cond else else_branch(())
    # canvas
    if tile == "functions/width":
        return lambda canvas: canvas.size[0]
    if tile == "functions/height":
        return lambda canvas: canvas.size[1]
    if tile == "functions/read":
        return lambda canvas: lambda x: lambda y: canvas.data[y][x]
    if tile == "functions/write":
        return lambda canvas: lambda x: lambda y: lambda value: canvas.set(x, y, value)
    
    # extensions
    if tile == "extensions/cos":
        return lambda x: math.cos(x)
    if tile == "extensions/sin":
        return lambda x: math.sin(x)
    if tile == "extensions/atan2":
        return lambda y: lambda x: math.atan2(y, x)
    
    print(f"Wrong side {direction} at {position(x,y)} for tile {tile} (or {tile} is not implemented)", file=sys.stderr)
    
labels = []
for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if tile == "label":
            icon = tile_data[y][x+1]
            value = get_value(x-1, y, "w", {})
            labels.append((icon, value))

mapping = {}
for y, row in enumerate(tile_data):
    for x, data in enumerate(row):
        found = None
        for icon, value in labels:
            if data == icon:
                found = value
                break
        if found is not None:
            mapping[(x, y)] = found
        
# copy of the input image
outimg = Image.open(program_file)
outdata = outimg.getdata()
outdata = [x for x in outdata]

for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
        if tile == "functions/entry":
            data, ret = get_value(x, y, "none", mapping)
            if data is None:
                print(f"Error: entry point at {position(x,y)} has no content", file=sys.stderr)
                continue
            if not isinstance(ret, Canvas):
                print(f"Error: entry point at {position(x,y)} has no canvas return", file=sys.stderr)
                continue
            if ret.position is None:
                print(f"Error: return canvas for entry point at {position(x,y)} has no position", file=sys.stderr)
                continue
            cx, cy = ret.position
            px = cx * base_grid + base_grid
            py = cy * base_grid + base_grid
            # for canvas data, we set the ret canvas
            if isinstance(data, Canvas):
                print(f"Entry point at ({position(x,y)}) evaluates to a canvas")
                # TODO: crop to canvas size
                for ty, row in enumerate(data.data):
                    for tx, value in enumerate(row):
                        pixel = red if value == 1 else white
                        outdata[(py+ty)*w + px+tx] = pixel
            elif isinstance(data, int) or isinstance(data, float):
                s = str(data)
                print(f"Entry point at ({position(x,y)}) evaluates to number {data}")
                for ci, c in enumerate(s):
                    tile = None
                    for name, value in number_tiles.items():
                        if value == c:
                            tile = name
                            break
                    if tile is None:
                        print(f"Error: character {c} not found in number tiles", file=sys.stderr)
                        continue
                    content = None
                    for name, data in library:
                        if name == tile:
                            content = data
                            break
                    if content is None:
                        print(f"Error: tile {tile} not found in library", file=sys.stderr)
                        continue
                    for idx, value in enumerate(content):
                        tx = idx % base_grid
                        ty = idx // base_grid
                        pixel = red if value == 1 else white
                        outdata[(py+ty)*w + px+ci*base_grid+tx] = pixel
            else:
                print(f"Entry point at ({position(x,y)}) evaluates to {data}")
                
            
outimg.putdata(outdata)
outimg.save(output_file)
