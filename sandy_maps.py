from hashlib import new
import random
from PIL import Image, ImageFont, ImageDraw
import numpy as np

class MapGenerator:
    def generate_terrain_map(self, start_size=4, level=7, water=100, mountain=180, snow=230) -> Image:
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
                self.convert_pixel(img,px,py,water,mountain,snow)
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

    def convert_pixel(self, im, ix, iy, water, mountain, snow):
        x, y, z = im.getpixel((ix,iy))
        if x < water:
            im.putpixel((ix,iy), (0,0,255))
        elif x > snow:
            im.putpixel((ix,iy), (255,255,255))
        elif x > mountain:
            im.putpixel((ix,iy), (128,128,128))
        else:
            im.putpixel((ix,iy), (0,255,0))
    
    def randomize_map_tiles(self, map):
        print("randomize_map_tiles")
        for y in range(map.height):
            for x in range(map.width):
                map.terrain[y][x].z = random.randint(0,255)

    def assign_map_tiles(self, map, water, mountain, snow):
        print("assign_map_tiles")
        for y in range(map.height):
            for x in range(map.width):
                z = map.terrain[y][x].z
                if z == -1:
                    map.terrain[y][x].t = "void"
                elif z < water:
                    map.terrain[y][x].t = "water"
                elif z > snow:
                    map.terrain[y][x].t = "snow"
                elif z > mountain:
                    map.terrain[y][x].t = "mountain"
                else:
                    map.terrain[y][x].t = "grass"

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

    def generate_terrain(self, start_size=4, level=7, water=100, mountain=180, snow=230):
        print("generate_terrain")
        tmap = Map(start_size, start_size)
        self.randomize_map_tiles(tmap)
        n = start_size
        for i in range(level):
            n = n * 2
            tmap = self.scale_up_map(tmap)
            # if i < level - 2:
            #     for px in range(n-1):
            #         for py in range(n-1):
            #             self.add_noise_one_pixel(img,px,py)
        self.assign_map_tiles(tmap, water, mountain, snow)
        return tmap
    
    def place_random_town(self, tmap):
        print("place_random_town")
        rpoint = (
            random.randint(2,tmap.width),
            random.randint(2,tmap.height)
        )
        rsize = (
            random.randint(1,5)*5,
            random.randint(1,5)*5
        )
        while self.check_placement(rpoint, rsize, tmap) is False:
            rpoint = (
                random.randint(2,tmap.width),
                random.randint(2,tmap.height)
            )
            rsize = (
                random.randint(1,5)*5,
                random.randint(1,5)*5
            )
        for y in range(rpoint[1], rpoint[1]+rsize[1]):
            for x in range(rpoint[0], rpoint[0]+rsize[0]):
                tmap.terrain[y][x].t = "town"
    
    def check_placement(self, point, size, tmap):
        print("check_placement "+str(point)+" "+str(size))
        for y in range(point[1], point[1]+size[1]):
            for x in range(point[0], point[0]+size[0]):
                if tmap.terrain[y][x].t != "grass":
                    return False
        print("placement good at "+str(point))
        return True

    def create_big_map(self):
        tmap = self.generate_terrain(start_size=4, level=10)
        towns = 5
        for i in range(towns):
            self.place_random_town(tmap)
        map = tmap.to_image()
        map.save("tmap.bmp")
    
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
                if tile == "grass":
                    color = (0,255,0)
                if tile == "water":
                    color = (0,0,255)
                if tile == "mountain":
                    color = (128,128,128)
                if tile == "snow":
                    color = (255,255,255)
                if tile == "town":
                    color = (255,128,0)
                img.putpixel((x,y), color)
        return img

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
    def __init__(self):
        self.buildings = []
    
