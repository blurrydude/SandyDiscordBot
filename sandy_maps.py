from hashlib import new
import math
import random
import traceback
from PIL import Image, ImageFont, ImageDraw
import numpy as np
from regex import P

class MapGenerator:
    def __init__(self, water=100, mountain=180, snow=230):
        self.water = water
        self.mountain = mountain
        self.snow = snow

    def generate_terrain_map(self, start_size=4, level=7) -> Image:
        img = self.random_img(start_size, start_size)
        n = start_size
        for i in range(level):
            n = n * 2
            newsize = (n, n)
            img = img.resize(newsize)
            if i < level - 2:
                for px in range(n-1):
                    for py in range(n-1):
                        self.add_noise_one_pixel(img,px,py)
                    
        for px in range(n):
            for py in range(n):
                self.convert_pixel(img,px,py)
        return img

    def random_img(self, width, height) -> Image:
        array = np.random.random_integers(0,255, (height,width,3))  
        array = np.array(array, dtype=np.uint8)
        img = Image.fromarray(array)
        return img

    def add_noise(self, x, mean, stddev) -> int:
        return round(min(max(0, x+random.normalvariate(mean,stddev)), 255))

    def add_noise_one_pixel(self, im, ix, iy, mean=0, stddev=5):
        x, y, z = im.getpixel((ix,iy))
        thing = self.add_noise(x, mean, stddev)
        im.putpixel((ix,iy), (thing,thing,thing))

    def convert_pixel(self, im, ix, iy):
        x, y, z = im.getpixel((ix,iy))
        if x < self.water:
            im.putpixel((ix,iy), (0,0,255))
        elif x > self.snow:
            im.putpixel((ix,iy), (255,255,255))
        elif x > self.mountain:
            im.putpixel((ix,iy), (128,128,128))
        else:
            im.putpixel((ix,iy), (0,255,0))
    
    def randomize_map_tiles(self, map):
        print("randomize_map_tiles")
        for y in range(map.height):
            for x in range(map.width):
                map.terrain[y][x].z = random.randint(0,255)

    def assign_map_tiles(self, map):
        print("assign_map_tiles")
        for y in range(map.height):
            for x in range(map.width):
                z = map.terrain[y][x].z
                map.terrain[y][x].t = self.get_terrain(z)

    def scale_up_map(self, map):
        print("scale_up_map")
        newmap = Map(map.width*2, map.height*2)
        for y in range(map.height):
            for x in range(map.width):
                newmap.terrain[y*2][x*2].z = map.terrain[y][x].z
        for y in range(newmap.height):
            for x in range(newmap.width):
                z = newmap.terrain[y][x].z
                if z == -1:
                    stuff = []
                    for sy in range(-1,2):
                        for sx in range(-1,2):
                            try:
                                sz = newmap.terrain[y+sy][x+sx].z
                                if sz > -1:
                                    stuff.append(sz)
                            except:
                                nada = True
                    avg = round(sum(stuff) / len(stuff))
                    newmap.terrain[y][x].z = avg
        return newmap

    def generate_terrain(self, start_size=4, level=7):
        print("generate_terrain")
        tmap = Map(start_size, start_size)
        self.randomize_map_tiles(tmap)
        n = start_size
        for i in range(level):
            n = n * 2
            tmap = self.scale_up_map(tmap)
            if i < level-3:
                for px in range(n-1):
                    for py in range(n-1):
                        if i < level - 4 or self.get_terrain(tmap.terrain[py][px].z) == "grass":
                            tmap.terrain[py][px].z = self.add_noise(tmap.terrain[py][px].z, 0, 5)
        self.assign_map_tiles(tmap)
        return tmap
    
    def place_random_town(self, tmap):
        print("place_random_town")
        s = random.randint(3,8)*5
        rpoint = (
            random.randint(2,tmap.width),
            random.randint(2,tmap.height)
        )
        rsize = (s,s)
        while self.check_placement(rpoint, rsize, tmap) is False:
            rpoint = (
                random.randint(2,tmap.width),
                random.randint(2,tmap.height)
            )
            rsize = (s,s)
        tmap.towns.append(Town(rpoint[0], rpoint[1], s))
        for y in range(rpoint[1], rpoint[1]+rsize[1]):
            for x in range(rpoint[0], rpoint[0]+rsize[0]):
                tmap.terrain[y][x].t = "town"
    
    def check_placement(self, point, size, tmap):
        print("check_placement "+str(point)+" "+str(size))
        for y in range(point[1], point[1]+size[1]):
            for x in range(point[0], point[0]+size[0]):
                try:
                    if tmap.terrain[y][x].t != "grass":
                        return False
                except:
                    return False
        print("placement good at "+str(point))
        return True
    
    def build_roads(self, tmap):
        tmap.towns.sort(key=lambda x: x.size, reverse=True)
        done = []
        town_count = len(tmap.towns)
        for v in range(0, town_count):
            town = tmap.towns[v]
            size = town.size
            connections = min(random.randint(1,size),town_count)
            other_towns = []
            for i in range(town_count):
                if i != v:
                    dest = tmap.towns[i]
                    distance = self.distance((town.x,town.y),(dest.x,dest.y))
                    other_towns.append({"town":dest,"distance":distance})
            other_towns.sort(key=lambda x: x["distance"])
            for i in range(connections):
                if [i,v] not in done and [v,i] not in done:
                    done.append([i,v])
                    start = (0,0)
                    end = (0,0)
                    if town.x < dest.x:
                        start = (town.x, town.y)
                        end = (dest.x, dest.y)
                    else:
                        start = (dest.x, dest.y)
                        end = (town.x, town.y)
                    road = self.build_road(tmap, start, end)
                    tmap.roads.append(road)

        # for v in range(0, len(tmap.towns)):
        #     for i in range(0, len(tmap.towns)):
        #         if i != v and [i,v] not in done and [v,i] not in done and tmap.towns[i].x < tmap.towns[v].x:
        #             road = self.build_road(
        #                 tmap,
        #                 # (tmap.towns[i].x, tmap.towns[i].y),
        #                 # (tmap.towns[v].x, tmap.towns[v].y)
        #                 (round(tmap.towns[i].x+(tmap.towns[i].size/2)), round(tmap.towns[i].y+(tmap.towns[i].size/2))),
        #                 (round(tmap.towns[v].x+(tmap.towns[v].size/2)), round(tmap.towns[v].y+(tmap.towns[v].size/2)))
        #             )
        #             tmap.roads.append(road)
        #             #self.rough_road(road, tmap)
        #             done.append([i,v])
        #self.rough_roads(tmap)

    def rough_roads(self, tmap):
        for road in tmap.roads:
            self.rough_road(road, tmap)

    def rough_road(self, road, tmap):
        for p in road:
            n = random.randint(1,4)
            e = random.randint(1,4)
            s = random.randint(1,4)
            w = random.randint(1,4)
            for i in range(1,n):
                try:
                    if tmap.terrain[p.y-i][p.x].t not in ["water", "snow", "town"]:
                        tmap.terrain[p.y-i][p.x].t = "path"
                except:
                    pass
            for i in range(1,e):
                try:
                    if tmap.terrain[p.y][p.x+i].t not in ["water", "snow", "town"]:
                        tmap.terrain[p.y][p.x+i].t = "path"
                except:
                    pass
            for i in range(1,s):
                try:
                    if tmap.terrain[p.y+i][p.x].t not in ["water", "snow", "town"]:
                        tmap.terrain[p.y+i][p.x].t = "path"
                except:
                    pass
            for i in range(1,w):
                try:
                    if tmap.terrain[p.y][p.x-i].t not in ["water", "snow", "town"]:
                        tmap.terrain[p.y][p.x-i].t = "path"
                except:
                    pass
    
    def get_terrain(self, z):
        if z == -1:
            return "void"
        elif z < self.water:
            return "water"
        elif z > self.snow:
            return "snow"
        elif z > self.mountain:
            return "mountain"
        else:
            return "grass"
    
    def get_slope(self, start_point, end_point):
        rise = end_point[1] - start_point[1]
        run = end_point[0] - start_point[0]
        if run == 0:
            slope = None
        else:
            slope = rise / run
        return slope
    
    def get_next_line_point(self, origin, destination):
        outside_points = [
            (origin[0]+1,origin[1]-1),
            (origin[0]+1,origin[1]),
            (origin[0]+1,origin[1]+1),
            (origin[0]-1,origin[1]-1),
            (origin[0]-1,origin[1]),
            (origin[0]-1,origin[1]+1),
            (origin[0],origin[1]-1),
            (origin[0],origin[1]+1)
        ]
        closest = 10000000.0
        cp = None
        for i in range(8):
            op = outside_points[i]
            distance = self.distance(op, destination)
            if distance < closest:
                closest = distance
                cp = op
        return cp
    def distance(self,pointa,pointb):
        return math.sqrt( ((pointa[0]-pointb[0])**2)+((pointa[1]-pointb[1])**2) )
    def build_road(self, tmap, start_point, end_point):
        ptr = start_point
        steps = 0
        road_points = []
        while ptr != end_point and steps < 2000:
            nlp = self.get_next_line_point(ptr,end_point)
            if nlp is None:
                steps = 2000
                continue
            d = self.get_direction(ptr, nlp)
            targs = self.get_path_targets(d.direction)
            steps = steps + 1
            try:
                if tmap.terrain[ptr[1]][ptr[0]].t not in ["water", "snow", "town"]:
                    tmap.terrain[ptr[1]][ptr[0]].t = "path"
                road_points.append(RoadTile(ptr[0],ptr[1],d.direction))
                options = []
                for t in targs:
                    tt = tmap.terrain[ptr[1]+t[1]][ptr[0]+t[0]]
                    if tt.t not in ["water", "snow"]:
                        options.append(tt)
                closest = self.get_closest_elevation(tmap.terrain[ptr[1]][ptr[0]],options)
                if closest == None:
                    options = []
                    co = self.get_counter_options(d.direction)
                    for t in co:
                        tt = tmap.terrain[ptr[1]+t[1]][ptr[0]+t[0]]
                        if tt.t not in ["water", "snow"]:
                            options.append(tt)
                    if len(options) == 0:
                        closest = MapTile(ptr[0]+d.mx,ptr[1]+d.my,0,0)
                    else:
                        closest = options[0]
                ptr = (closest.x,closest.y)
            except Exception as e: 
                error = str(e)
                tb = traceback.format_exc()
                print(error)
                do_nada = True
                ptr = (ptr[0]+d.mx,ptr[1]+d.my)
        return road_points
    
    def get_counter_options(self, direction):
        if direction == "e" or direction == "w":
            return [(1,0),(-1,0)]
        elif direction == "se" or direction == "nw":
            return [(1,-1),(-1,1)]
        elif direction == "s" or direction == "n":
            return [(0,1),(0,-1)]
        elif direction == "sw" or direction == "ne":
            return [(1,1),(-1,-1)]
        return []

    def build_road_line(self, tmap, start_point, end_point):
        ptr = start_point
        steps = 0
        road_points = []
        while ptr != end_point and steps < 2000:
            d = self.get_direction(ptr, end_point)
            steps = steps + 1
            try:
                if tmap.terrain[ptr[1]+(d.my*2)][ptr[0]+(d.mx*2)].t == "path":
                    steps = 1000
                elif tmap.terrain[ptr[1]][ptr[0]].t not in ["town", "water", "snow", "path"]:
                    tmap.terrain[ptr[1]][ptr[0]].t = "path"
                    road_points.append(RoadTile(ptr[0],ptr[1],d.direction))
            except:
                print("BAD")
                do_nada = True
            ptr = (ptr[0]+d.mx,ptr[1]+d.my)
        return road_points
    
    def get_direction(self, origin, destination):
        mx = 0
        my = 0
        if origin[0] < destination[0]:
            mx = 1
        if origin[0] > destination[0]:
            mx = -1
        if origin[1] < destination[1]:
            my = 1
        if origin[1] > destination[1]:
            my = -1
        ns = ""
        ew = ""
        if mx == -1:
            ew = "w"
        elif mx == 1:
            ew = "e"
        if my == -1:
            ns = "n"
        elif my == 1:
            ns = "s"
        direction = ns + ew
        return Direction(direction, mx, my)
    
    def get_closest_elevation(self, origin, options):
        closest_d = 255
        closest_p = None
        for option in options:
            d =  abs(origin.z - option.z)
            if d < closest_d:
                closest_d = d
                closest_p = option
        return closest_p
    
    def get_path_targets(self,direction):
        targ = []
        if direction == "nw":
            targ = [(-1,0),(-1,-1),(0,-1)]
        elif direction == "n":
            targ = [(-1,-1),(0,-1),(1,-1)]
        elif direction == "ne":
            targ = [(0,-1),(1,-1),(1,0)]
        elif direction == "w":
            targ = [(-1,-1),(-1,0),(-1,1)]
            
        elif direction == "e":
            targ = [(1,-1),(1,0),(1,1)]
        elif direction == "sw":
            targ = [(-1,0),(-1,1),(0,1)]
        elif direction == "s":
            targ = [(-1,1),(0,1),(1,1)]
        elif direction == "se":
            targ = [(0,1),(1,1),(1,0)]
        return targ

    def create_big_map(self, towns):
        tmap = self.generate_terrain(start_size=4, level=8)
        for i in range(towns):
            self.place_random_town(tmap)
        self.build_roads(tmap)
        map = tmap.to_image()
        map.save("tmap.png")

class Direction:
    def __init__(self, direction, mx, my):
        self.direction = direction
        self.mx = mx
        self.my = my

class RoadTile:
    def __init__(self, x, y, d):
        self.x = x
        self.y = y
        self.d = d
    
class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.terrain = []
        for y in range(height):
            self.terrain.append([])
            for x in range(width):
                self.terrain[y].append(MapTile(x,y,-1,"void"))
        self.roads = []
        self.towns = []
        self.territories = []
    
    def to_image(self):
        print("to_image")
        img = Image.new(mode="RGB", size=(self.width, self.height))
        for y in range(self.height):
            for x in range(self.width):
                color = (0,0,0)
                tile = self.terrain[y][x].t
                noisy = True
                if tile == "path":
                    color = (72,64,0)
                elif tile == "grass":
                    color = (0,255,0)
                elif tile == "water":
                    noisy = False
                    color = (0,0,255)
                elif tile == "mountain":
                    color = (128,128,128)
                elif tile == "snow":
                    noisy = False
                    color = (255,255,255)
                if tile != "town":
                    if noisy is True:
                        img.putpixel((x,y), self.noisy_color(color,stddev=10))
                    else:
                        img.putpixel((x,y), color)
        for y in range(self.height):
            for x in range(self.width):
                color = (0,0,0)
                tile = self.terrain[y][x].t
                if tile == "town":
                    color = (255,128,0)
                    img.putpixel((x,y), color)
        return img

    def noisy_color(self, color, mean=0, stddev=5):
        r = self.add_noise(color[0], mean, stddev)
        g = self.add_noise(color[1], mean, stddev)
        b = self.add_noise(color[2], mean, stddev)
        return (r,g,b)

    def add_noise(self, x, mean, stddev) -> int:
        return round(min(max(0, x+random.normalvariate(mean,stddev)), 255))

class MapTile:
    def __init__(self, x, y, z, t):
        self.x = x
        self.y = y
        self.z = z
        self.t = t

class Building:
    def __init__(self, size):
        self.size = size

class Town:
    def __init__(self, x, y, size):
        self.buildings = []
        self.x = x
        self.y = y
        self.size = size
    
