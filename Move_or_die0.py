import pygame, sys, math
from queue import PriorityQueue
from random import randint, random, choice
from dataclasses import dataclass

pygame.init()

CELL, COLS, ROWS = 24, 48, 24
HUD_H = 40
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL + HUD_H
FPS = 60

BG = (18,18,30)
GRID = (40,40,50)
WALL = (60,60,80)
PLAYER_C = (80,200,240)
ENEMY_C = (240,100,100)
PU_C = {"freeze":(160,160,255), "teleport":(255,200,120)}
TEXT = (220,220,220)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)
bigfont = pygame.font.SysFont(None, 28)

def heuristic(a,b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def neigh(grid, c):
    x,y=c
    out=[]
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx,ny=x+dx,y+dy
        if 0<=nx<COLS and 0<=ny<ROWS and grid[ny][nx]==0:
            out.append((nx,ny))
    return out

def a_star(grid, s, g, bias):
    pq=PriorityQueue()
    pq.put((0,s))
    came={}
    dist={s:0}
    vis=set()
    while not pq.empty():
        _,cur=pq.get()
        if cur==g:
            path=[]
            while cur in came:
                path.append(cur)
                cur=came[cur]
            path.reverse()
            return path
        if cur in vis: continue
        vis.add(cur)
        for n in neigh(grid, cur):
            d=dist[cur]+1
            if d < dist.get(n,1e9):
                came[n]=cur
                dist[n]=d
                b=((n[0]*COLS+n[1])%10)/10
                pq.put((d+heuristic(n,g)+bias*b, n))
    return []

def make_grid(d=0.12):
    return [[1 if random()<d else 0 for _ in range(COLS)] for _ in range(ROWS)]

def free_cell(g):
    for _ in range(8000):
        x,y=randint(1,COLS-2),randint(1,ROWS-2)
        if g[y][x]==0: return (x,y)
    return (1,1)

def clear(g, c, r=2):
    x,y=c
    for dy in range(-r,r+1):
        for dx in range(-r,r+1):
            nx,ny=x+dx,y+dy
            if 0<=nx<COLS and 0<=ny<ROWS:
                g[ny][nx]=0

@dataclass
class Player:
    grid: list
    cell: list
    cd: int = 120
    size: float = CELL*0.7

    def __post_init__(self):
        x,y=self.cell
        self.pos=pygame.Vector2(x*CELL+CELL/2,y*CELL+CELL/2)
        self.target=self.pos.copy()
        self.last_move=0

    def update(self,dt):
        if self.pos.distance_to(self.target)>0.5:
            d=self.target-self.pos
            t=max(self.cd/1000,0.001)
            v=d/t*dt
            self.pos = self.target.copy() if v.length_squared()>=d.length_squared() else self.pos+v

    def move(self,dx,dy):
        now=pygame.time.get_ticks()
        if now-self.last_move<self.cd: return
        x,y=self.cell[0]+dx,self.cell[1]+dy
        if 0<=x<COLS and 0<=y<ROWS and self.grid[y][x]==0:
            self.cell=[x,y]
            self.target=pygame.Vector2(x*CELL+CELL/2,y*CELL+CELL/2)
            self.last_move=now

    def draw(self,s):
        r=pygame.Rect(0,0,self.size,self.size)
        r.center=(int(self.pos.x),int(self.pos.y))
        pygame.draw.rect(s,PLAYER_C,r,border_radius=6)

    def teleport(self,c):
        self.cell=[c[0],c[1]]
        self.pos=pygame.Vector2(c[0]*CELL+CELL/2,c[1]*CELL+CELL/2)
        self.target=self.pos.copy()
        self.last_move=pygame.time.get_ticks()

@dataclass
class Enemy:
    grid: list
    cell: list
    player: Player

    def __post_init__(self):
        x,y=self.cell
        self.pos=pygame.Vector2(x*CELL+CELL/2,y*CELL+CELL/2)
        self.path=[]
        self.i=0
        self.speed=95
        self.freeze_end=0
        self.recalc=10
        self.count=0
        self.bias=random()*0.8

    def update(self,dt,t):
        now=pygame.time.get_ticks()
        if now<self.freeze_end: return
        self.speed=90*(1+t/100)
        self.count+=1
        if self.count>=self.recalc or not self.path:
            s=(self.cell[0],self.cell[1])
            g=(self.player.cell[0],self.player.cell[1])
            self.path=a_star(self.grid,s,g,self.bias)
            self.i=0
            self.count=0
        if self.path and self.i<len(self.path):
            nx,ny=self.path[self.i]
            target=pygame.Vector2(nx*CELL+CELL/2,ny*CELL+CELL/2)
            d=target-self.pos
            if d.length()<1:
                self.pos=target.copy()
                self.cell=[nx,ny]
                self.i+=1
            else:
                step=d.normalize()*(self.speed*dt)
                if step.length_squared()>=d.length_squared():
                    self.pos=target.copy()
                    self.cell=[nx,ny]
                    self.i+=1
                else:
                    self.pos+=step

    def draw(self,s):
        r=pygame.Rect(0,0,CELL*0.7,CELL*0.7)
        r.center=(int(self.pos.x),int(self.pos.y))
        pygame.draw.rect(s,ENEMY_C,r,border_radius=6)

    def teleport(self,c):
        self.cell=[c[0],c[1]]
        self.pos=pygame.Vector2(c[0]*CELL+CELL/2,c[1]*CELL+CELL/2)
        self.i=0
        self.path=[]

    def freeze(self,ms):
        self.freeze_end=pygame.time.get_ticks()+ms

@dataclass
class PowerUp:
    grid: list
    kind: str
    cell: tuple

    def __post_init__(self):
        self.pos=(self.cell[0]*CELL+CELL/2,self.cell[1]*CELL+CELL/2)
        self.r=CELL*0.34
        self.spawn=pygame.time.get_ticks()
        self.life=14000

    def draw(self,s):
        pygame.draw.circle(s,PU_C[self.kind],(int(self.pos[0]),int(self.pos[1])),int(self.r))
        t=font.render(self.kind[0].upper(),True,(0,0,0))
        s.blit(t,t.get_rect(center=(int(self.pos[0]),int(self.pos[1]))))

    def expired(self):
        return pygame.time.get_ticks()-self.spawn>self.life

def main():
    grid=make_grid()
    p=free_cell(grid); clear(grid,p,2)
    e=free_cell(grid); clear(grid,e,2)

    player=Player(grid,list(p))
    enemies=[Enemy(grid,list(e),player)]
    power=[]

    last=0
    interval=5000
    best=0
    start=pygame.time.get_ticks()

    running=True
    while running:
        dt=clock.tick(FPS)/1000
        now=pygame.time.get_ticks()
        t=(now-start)/1000

        if t>=15 and len(enemies)==1:
            c=free_cell(grid); clear(grid,c,1)
            enemies.append(Enemy(grid,list(c),player))

        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: running=False
            elif ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: running=False
                if ev.key==pygame.K_LEFT: player.move(-1,0)
                if ev.key==pygame.K_RIGHT: player.move(1,0)
                if ev.key==pygame.K_UP: player.move(0,-1)
                if ev.key==pygame.K_DOWN: player.move(0,1)

        if now-last>interval:
            last=now
            interval=randint(4000,9000)
            kind=choice(["freeze","teleport","freeze"])
            c=free_cell(grid); clear(grid,c,0)
            power.append(PowerUp(grid,kind,c))

        player.update(dt)
        for en in enemies: en.update(dt,t)

        if len(enemies)>1:
            e1,en2=enemies[0],enemies[1]
            if e1.pos.distance_to(en2.pos)<CELL:
                c=free_cell(grid); clear(grid,c,1)
                en2.teleport(c)

        rem=[]
        for pu in power:
            if pu.expired(): rem.append(pu)
            px,py=player.cell
            if (px,py)==pu.cell or math.hypot(player.pos.x-pu.pos[0],player.pos[1]-pu.pos[1])<CELL*0.6:
                if pu.kind=="freeze":
                    for en in enemies: en.freeze(3000)
                else:
                    c=free_cell(grid); clear(grid,c,1)
                    player.teleport(c)
                rem.append(pu)

        for r in rem: power.remove(r)

        for en in enemies:
            if player.pos.distance_to(en.pos)<CELL*0.6:
                best=max(best,t)
                grid=make_grid()
                p=free_cell(grid); clear(grid,p,2)
                e=free_cell(grid); clear(grid,e,2)
                player=Player(grid,list(p))
                enemies=[Enemy(grid,list(e),player)]
                power=[]
                start=pygame.time.get_ticks()
                break

        screen.fill(BG)

        for y in range(ROWS):
            for x in range(COLS):
                r=pygame.Rect(x*CELL,y*CELL,CELL,CELL)
                if grid[y][x]: pygame.draw.rect(screen,WALL,r)
                pygame.draw.rect(screen,GRID,r,1)

        for pu in power: pu.draw(screen)
        player.draw(screen)
        for en in enemies: en.draw(screen)

        pygame.draw.rect(screen,(12,12,18),(0,ROWS*CELL,WIDTH,HUD_H))
        screen.blit(bigfont.render("MOVE OR DIE",True,TEXT),(8,ROWS*CELL+5))
        screen.blit(font.render(f"Time: {t:.2f}s",True,PLAYER_C),(230,ROWS*CELL+8))
        screen.blit(font.render(f"Best: {best:.2f}s",True,ENEMY_C),(230,ROWS*CELL+24))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
