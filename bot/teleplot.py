import matplotlib.pyplot as plt
import json
import numpy as np
from random import randint

randstr = ''
for i in range(ord('a'),ord('z')+1):
    randstr += chr(i)
for i in range(ord('A'),ord('Z')+1):
    randstr += chr(i)
for i in range(ord('0'),ord('9')+1):
    randstr += chr(i)

def randname():
    s = ''
    for n in range(25):
        index = randint(0, len(randstr)-1)
        s += randstr[index]
    return s

def plotjson(jtxt):
    outimg = 'image-'+randname()+'.png'
    jdata = json.loads(jtxt)
    plt.clf()
    for dataset in jdata["datasets"]:
        data = np.array(dataset["data"])
        x, y = data[:,0], data[:,1]
        plt.plot(x, y, label=dataset["name"])
    plt.legend()
    plt.savefig(outimg)
    return outimg

if __name__ == "__main__":
    with open("test.json", "r") as fd:
        image = plotjson(fd.read())
        print("image:",image)
