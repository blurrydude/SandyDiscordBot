from PIL import Image
import random

def get_random_height_map(size):
    height_map = []
    for y in range(size):
        height_map.append([])
        for x in range(size):
            value = random.randint(0,255)
            height_map[y].append(value)
    return height_map

def double_height_map_scale(original_map):
    original_size = len(original_map)
    new_size = original_size * 2
    new_map = [[]] * new_size
    for y in range(new_size):
        new_map[y] = [0] * new_size
    
    for y in range(original_size):
        for x in range(original_size):
            new_map[y*2][x*2] = original_map[y][x]
    
    for y in range(new_size):
        for x in range(new_size):
            value = new_map[y][x]
            if value == 0:
                new_map[y][x] = get_average_surrounding_values(new_map,(x,y))
    
    return new_map

def get_average_surrounding_values(height_map, point):
    x = point[0]
    y = point[1]
    limit = len(height_map) - 2
    values = [
        height_map[y-1][x-1],
        height_map[y-1][x],
        height_map[y][x-1]
    ]
    if x <= limit:
        height_map[y-1][x+1]
        height_map[y][x+1]
    if y <= limit:
        height_map[y+1][x-1]
        height_map[y+1][x]
    if x <= limit and y <= limit:
        height_map[y+1][x+1]
    to_average = []
    for value in values:
        if value > 0:
            to_average.append(value)
    return round(sum(to_average) / len(to_average))

# this one's special. It modifies in place.
def add_noise(height_map, level):
    size = len(height_map)
    for y in range(size):
        for x in range(size):
            value = height_map[y][x]
            adjustment = random.randint(0,level*2) - level
            new_value = min(255,max(0,value + adjustment))
            height_map[y][x] = new_value

def get_image_from_height_map(height_map) -> Image:
    size = len(height_map)
    img = Image.new(mode="RGB", size=(size,size))
    for y in range(size):
        for x in range(size):
            value = height_map[y][x]
            img.putpixel((x,y),(value,value,value))
    return img

def make_map(height_map, water=100, mountain=180, snow=230) -> Image:
    size = len(height_map)
    img = Image.new(mode="RGB", size=(size,size))
    for y in range(size):
        for x in range(size):
            value = height_map[y][x]
            if value < water:
                img.putpixel((x,y),(0,0,255))
            elif value > snow:
                img.putpixel((x,y),(255,255,255))
            elif value > mountain:
                img.putpixel((x,y),(128,128,128))
            else:
                img.putpixel((x,y),(0,255,0))
    return img

# this one's special. It modifies in place.
def despeckle(img):
    size = img.size[0] # since we're square
    limit = size - 2
    for y in range(1,limit):
        for x in range(1,limit):
            p = img.getpixel((x,y))
            neighbors = [
                img.getpixel((x-1,y-1)),
                img.getpixel((x-1,y)),
                img.getpixel((x-1,y+1)),
                img.getpixel((x+1,y-1)),
                img.getpixel((x+1,y)),
                img.getpixel((x+1,y+1)),
                img.getpixel((x,y-1)),
                img.getpixel((x,y+1))
            ]
            all_the_same = True
            for i in range(7):
                if neighbors[i] != neighbors[7]:
                    all_the_same = False
            if p != neighbors[7] and all_the_same == True:
                img.putpixel((x,y), neighbors[7])

if __name__ == "__main__":
    map = get_random_height_map(8)
    get_image_from_height_map(map).show()
    for i in range(6):
        map = double_height_map_scale(map)
        get_image_from_height_map(map).show()
        if i < 4:
            add_noise(map, 25)
            get_image_from_height_map(map).show()
    img = make_map(map)
    img.show()
    despeckle(img)
    img.show()