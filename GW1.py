import sys
import math
import json
import pygame

STATE_MENU="MENU"
STATE_SETTINGS="SETTINGS"
STATE_SAVELOAD="SAVELOAD"
STATE_PLAY="PLAY"
FPS=60
G=1
PLANET_RADIUS_RANGE=(10,200)
PLANET_DENSITY_RANGE=(1,100)
BULLET_RADIUS_RANGE=(2,20)
BULLET_DENSITY_RANGE=(1,50)
DRAG_SCALE_RANGE=(1,100)
FRICTION_RANGE=(0,100)
SETTINGS_FILE="settings.json"
GAME_SAVE_FILE="savegame.json"

class Settings:
    def __init__(self):
        self.planet_radius=30
        self.planet_density=10
        self.bullet_radius=5
        self.bullet_density=1
        self.drag_scale=20
        self.friction=0
    @property
    def planet_mass(self):
        return self.planet_density*(self.planet_radius**2)
    def to_dict(self):
        return {"planet_radius":self.planet_radius,
                "planet_density":self.planet_density,
                "bullet_radius":self.bullet_radius,
                "bullet_density":self.bullet_density,
                "drag_scale":self.drag_scale,
                "friction":self.friction}
    def save(self,filename=SETTINGS_FILE):
        with open(filename,"w") as f:
            json.dump(self.to_dict(),f,indent=2)
    def load(self,filename=SETTINGS_FILE):
        with open(filename,"r") as f:
            data=json.load(f)
        for k,v in data.items():
            if hasattr(self,k):
                rng=globals().get(k.upper()+"_RANGE")
                if rng:
                    lo,hi=rng
                    setattr(self,k,max(lo,min(hi,v)))
                else:
                    setattr(self,k,v)

class Projectile:
    def __init__(self,pos,vel,radius):
        self.pos=pygame.math.Vector2(pos)
        self.vel=pygame.math.Vector2(vel)
        self.radius=radius
        self.active=True
        self.arc_time=0.0
    def update(self,dt,pr,pm,fr):
        if not self.active: return
        self.arc_time+=dt
        d=CENTER-self.pos
        dist=d.length()
        if dist<=pr+self.radius or dist>MAX_DIST:
            self.active=False
            return
        self.vel+=d.normalize()*(G*pm/(dist*dist))*dt
        self.vel*=(1-fr/100.0*dt)
        self.pos+=self.vel*dt
    def draw(self,surf):
        pygame.draw.circle(surf,(255,255,255),(int(self.pos.x),int(self.pos.y)),self.radius)

def simulate_trajectory(start,vel,pr,pm,fr,steps=200,dt=1/60.0):
    pos=pygame.math.Vector2(start)
    v=pygame.math.Vector2(vel)
    path=[]
    for _ in range(steps):
        d=CENTER-pos
        dist=d.length()
        if dist<=pr or dist>MAX_DIST: break
        v+=d.normalize()*(G*pm/(dist*dist))*dt
        v*=(1-fr/100.0*dt)
        pos+=v*dt
        path.append((int(pos.x),int(pos.y)))
    return path

def save_game():
    data={"settings":settings.to_dict(),
          "bullets":[{"pos":[b.pos.x,b.pos.y],"vel":[b.vel.x,b.vel.y],"radius":b.radius,"arc_time":b.arc_time} for b in bullets],
          "score":total_score}
    with open(GAME_SAVE_FILE,"w") as f:
        json.dump(data,f,indent=2)

def load_game():
    global bullets,total_score
    with open(GAME_SAVE_FILE,"r") as f:
        data=json.load(f)
    if "settings" in data: settings.load()
    total_score=data.get("score",0.0)
    bullets=[]
    for rec in data.get("bullets",[]):
        b=Projectile(rec["pos"],rec["vel"],rec["radius"])
        b.arc_time=rec.get("arc_time",0.0)
        bullets.append(b)

pygame.init()
screen=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
WIDTH,HEIGHT=screen.get_size()
CENTER=pygame.math.Vector2(WIDTH/2,HEIGHT/2)
MAX_DIST=max(WIDTH,HEIGHT)*1.5
clock=pygame.time.Clock()
font=pygame.font.SysFont(None,36)
small=pygame.font.SysFont(None,24)

menu_items=["Start Game","Settings","Save/Load","Quit"]
save_items=["Save Game","Load Game","Back"]
settings_items=["Planet Radius","Planet Density","Bullet Radius","Bullet Density","Drag Scale","Friction","Save Settings","Load Settings","Back"]

settings=Settings()
state=STATE_MENU
menu_idx=0
save_idx=0
settings_idx=0
bullets=[]
total_score=0.0
paused=False
dragging=False
drag_start=pygame.math.Vector2(0,0)

while True:
    dt=clock.tick(FPS)/1000.0
    mx,my=pygame.mouse.get_pos()
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT: pygame.quit();sys.exit()
        if state==STATE_PLAY and ev.type==pygame.KEYDOWN and ev.key==pygame.K_p:
            paused=not paused
        if state==STATE_MENU:
            if ev.type==pygame.MOUSEMOTION:
                for i,it in enumerate(menu_items):
                    r=font.render(it,True,(255,255,255)).get_rect(center=(CENTER.x,200+i*50))
                    if r.collidepoint(mx,my): menu_idx=i
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                c=menu_items[menu_idx]
                if c=="Start Game": state=STATE_PLAY;bullets.clear();total_score=0.0;paused=False
                elif c=="Settings": state=STATE_SETTINGS
                elif c=="Save/Load": state=STATE_SAVELOAD
                elif c=="Quit": pygame.quit();sys.exit()
            if ev.type==pygame.KEYDOWN:
                if ev.key in (pygame.K_UP,pygame.K_DOWN): menu_idx=(menu_idx+(1 if ev.key==pygame.K_DOWN else -1))%len(menu_items)
                elif ev.key==pygame.K_RETURN:
                    c=menu_items[menu_idx]
                    if c=="Start Game": state=STATE_PLAY;bullets.clear();total_score=0.0;paused = False
                    elif c=="Settings": state=STATE_SETTINGS
                    elif c=="Save/Load": state=STATE_SAVELOAD
                    elif c=="Quit": pygame.quit();sys.exit()
                elif ev.key==pygame.K_ESCAPE:  state = STATE_PLAY;paused = False
        elif state==STATE_SETTINGS:
            if ev.type==pygame.MOUSEMOTION:
                for i,it in enumerate(settings_items):
                    text=it if it in("Save Settings","Load Settings","Back") else f"{it}: {getattr(settings,it.lower().replace(' ', '_'))}"
                    r=font.render(text,True,(255,255,255)).get_rect(topleft=(100,150+i*50))
                    if r.collidepoint(mx,my): settings_idx=i
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                key=settings_items[settings_idx]
                if key=="Back": state=STATE_MENU
                elif key=="Save Settings": settings.save()
                elif key=="Load Settings": settings.load()
                else:
                    text=f"{key}: {getattr(settings,key.lower().replace(' ', '_'))}"
                    r=font.render(text,True,(255,255,255)).get_rect(topleft=(100,150+settings_idx*50))
                    delta=-1 if mx<r.centerx else 1
                    attr=key.lower().replace(' ','_')
                    lo,hi=globals()[attr.upper()+"_RANGE"]
                    setattr(settings,attr,max(lo,min(hi,getattr(settings,attr)+delta)))
            if ev.type==pygame.KEYDOWN:
                if ev.key in (pygame.K_UP,pygame.K_DOWN): settings_idx=(settings_idx+(1 if ev.key==pygame.K_DOWN else -1))%len(settings_items)
                elif ev.key in (pygame.K_LEFT,pygame.K_RIGHT):
                    key=settings_items[settings_idx]
                    if key not in("Save Settings","Load Settings","Back"):
                        attr=key.lower().replace(' ','_')
                        lo,hi=globals()[attr.upper()+"_RANGE"]
                        change=-1 if ev.key==pygame.K_LEFT else 1
                        setattr(settings,attr,max(lo,min(hi,getattr(settings,attr)+change)))
                elif ev.key==pygame.K_RETURN and settings_items[settings_idx]=="Back": state=STATE_MENU
                elif ev.key==pygame.K_ESCAPE: state=STATE_MENU
        elif state==STATE_SAVELOAD:
            if ev.type==pygame.MOUSEMOTION:
                for i,it in enumerate(save_items):
                    r=font.render(it,True,(255,255,255)).get_rect(center=(CENTER.x,200+i*50))
                    if r.collidepoint(mx,my): save_idx=i
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                c=save_items[save_idx]
                if c=="Save Game": save_game()
                elif c=="Load Game": load_game();state=STATE_PLAY
                elif c=="Back": state=STATE_MENU
            if ev.type==pygame.KEYDOWN:
                if ev.key in (pygame.K_UP,pygame.K_DOWN): save_idx=(save_idx+(1 if ev.key==pygame.K_DOWN else -1))%len(save_items)
                elif ev.key==pygame.K_RETURN:
                    c=save_items[save_idx]
                    if c=="Save Game": save_game()
                    elif c=="Load Game": load_game();state=STATE_PLAY
                    elif c=="Back": state=STATE_MENU
                elif ev.key==pygame.K_ESCAPE: state=STATE_MENU
        elif state==STATE_PLAY:
            if not paused:
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    dragging=True;drag_start=pygame.math.Vector2(ev.pos)
                if ev.type==pygame.MOUSEBUTTONUP and ev.button==1 and dragging:
                    dragging=False
                    drag_end=pygame.math.Vector2(ev.pos)
                    vel=(drag_start-drag_end)*(settings.drag_scale/10)
                    bullets.append(Projectile(drag_start,vel,settings.bullet_radius))
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: state=STATE_MENU
    if state==STATE_PLAY and not paused:
        for b in bullets[:]:
            b.update(dt,settings.planet_radius,settings.planet_mass,settings.friction)
            if b.active and b.arc_time>20: total_score+=dt
            if not b.active: bullets.remove(b)
    screen.fill((0,0,0))
    if state==STATE_MENU:
        for i,it in enumerate(menu_items):
            color=(255,255,0) if i==menu_idx else (200,200,200)
            screen.blit(font.render(it,True,color),font.render(it,True,color).get_rect(center=(CENTER.x,200+i*50)))
    elif state==STATE_SETTINGS:
        for i,it in enumerate(settings_items):
            text=it if it in("Save Settings","Load Settings","Back") else f"{it}: {getattr(settings,it.lower().replace(' ','_'))}"
            color=(255,255,0) if i==settings_idx else (200,200,200)
            screen.blit(font.render(text,True,color),font.render(text,True,color).get_rect(topleft=(100,150+i*50)))
    elif state==STATE_SAVELOAD:
        for i,it in enumerate(save_items):
            color=(255,255,0) if i==save_idx else (200,200,200)
            screen.blit(font.render(it,True,color),font.render(it,True,color).get_rect(center=(CENTER.x,200+i*50)))
    elif state==STATE_PLAY:
        pygame.draw.circle(screen,(0,100,255),(int(CENTER.x),int(CENTER.y)),settings.planet_radius)
        if not paused and dragging:
            de=pygame.mouse.get_pos()
            vel=(drag_start-pygame.math.Vector2(de))*(settings.drag_scale/10)
            path=simulate_trajectory(drag_start,vel,settings.planet_radius,settings.planet_mass,settings.friction)
            if len(path)>1: pygame.draw.lines(screen,(100,255,100),False,path,2)
            pygame.draw.line(screen,(200,200,200),drag_start,de,2)
        for b in bullets: b.draw(screen)
        screen.blit(font.render(f"Score: {int(total_score)}",True,(255,255,255)),(10,10))
        if paused: screen.blit(font.render("Paused",True,(255,0,0)),(WIDTH//2-50,10))
    pygame.display.flip()
# End of main loop
pygame.quit()
sys.exit()
