#main file of the circular track (hard mode), all functions controlling user/computer players

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
import sys
import math
import random
import numpy as np  #配列
import os  #ファイル作成

def displayBigText(txt, position, color, shad = (0,0,0,1)):
    size = 0.25
    display = OnscreenText(text = txt, fg = color, scale = size, 
                    shadow = shad, parent=base.a2dTopLeft, 
                    pos=position, align=TextNode.ALeft)
    return display

def displaySmallText(txt, position, color, shad = None):
    size = 0.1
    display = OnscreenText(text = txt, fg = color, scale = size, shadow = shad, 
                        parent=base.a2dTopLeft, pos=position, align=TextNode.ALeft)
    return display


def distance(x1,y1,x2,y2):
    return ( (x1-x2)**2 + (y1-y2)**2 )**0.5

def roundtoThou(n):
    return math.ceil(n * 1000.0)/1000.0

class Game(ShowBase):
 
    def __init__(self):
        ShowBase.__init__(self)
        
        #countdown sound file from https://www.youtube.com/watch?v=KOoCEIwswYg
        self.cdMusic = loader.loadSfx("sounds/countdown.ogg")
        #race sound file from https://www.youtube.com/watch?v=eawQqkq8ROo
        self.rMusic = loader.loadSfx("sounds/race.ogg")
        
        self.r_1 = 600
        self.r_2 = 750
        self.rad_avg = (self.r_1 + self.r_2) / 2
        self.rad_incr = (self.r_2 - self.r_1) / 3
        
        #window and camera
        self.win.setClearColor((0, 0, 0, 1))
        self.startPos = LPoint3f(100, 50, 0)
        self.disableMouse()
        self.x = self.startPos.getX()
        self.y = self.startPos.getY()
        self.z = 15
        self.camera.setPos(-50,50,250)
        #self.camera.setPos(self.r_1 + self.rad_incr, 10, 300)
        self.camera.setH(0)
        self.camMaxDist = 180
        self.camMinDist = 150
        
        #mario character (user player)
        #3d mario model file from past tp, with permission:
        #https://github.com/Kabartchlett/15-112-Term-Project
        self.mario = Actor("models/marioKart")
        self.scale = 7
        self.mario.setScale(self.scale)
        self.mario.setH(self.mario, 90)
        self.mario.reparentTo(render)
        self.marioX = 3
        #self.marioY = self.startPos.getY() /3
        self.marioY = 10
        self.marioZ = 15
        #self.mario.setPos(self.r_1 + self.rad_incr,-40,15)
        self.mario.setPos(3,50,15)
        self.mario.y_speed = 0
        self.mario.h_speed = 0
        self.mario.raceTime = 0
        self.mario.finishTime = 0
        self.drifted = False
        self.mario.numFellOff = 0
        self.mario.falling = False
        self.mario.startFallTime = None
        self.mario.startFallPos = None
        self.mario.gameover = False
        self.mario_lapText = None
        self.mario.crossed = True
        self.mario.lap = 1
        
        #floater method from roaming ralph:
        #https://github.com/panda3d/panda3d/tree/master/samples/roaming-ralph
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.mario)
        self.floater.setZ(2)
        
        self.center = NodePath(PandaNode("center"))
        self.center.setZ(0)
        self.center.setZ(0)
        self.center.setZ(15)
        
        #computer player
        #3d yoshi model file from past tp, with permission:
        #https://github.com/Kabartchlett/15-112-Term-Project
        self.yoshi = Actor("models/yoshiKart")
        self.yoshi.setScale(self.scale)
        self.yoshi.setH(self.yoshi, 90)
        self.yoshi.reparentTo(render)
        self.yoshiX = 3
        self.yoshiY = self.startPos.getY() *(2/3)
        self.yoshiZ = 10
        self.yoshi.setPos(3,100,15)
        #self.yoshi.setPos(self.r_1 + 2*self.rad_incr,-40,15)
        self.yoshi.y_speed = -25
        self.yoshi.h_speed = 0
        self.AIadjust = 60
        self.yoshi.raceTime = 0
        self.yoshi.finishTime = 0
        self.yoshi.numFellOff = 0
        self.yoshi.falling = False
        self.yoshi.startFallTime = None
        self.yoshi.startFallPos = None
        self.yoshiStartH = None
        self.yoshi.gameover = False
        self.yoshi_lapText = None
        self.yoshi.crossed = True
        self.yoshi.lap = 1
        
        #statuses
        self.victory = False
        self.loss = False
        self.menuCount = 0
        self.paused = False
        self.addMove = 1
        self.timeDelay = 0
        self.start = True
        self.escapeStart = False
        self.menuStart = True
        self.charFin = True
        self.counting = True
        self.playing = True
        self.playRaceMusic = False
        self.menuDisplayed = False
        
        #data init
        self.vDataRows = 100
        self.finalX = self.x
        self.lines = []
        self.isPaused = []
        self.wait = 10
        self.countdowns = []
        self.startText = []
        self.cirNodePath = None
        self.OSimageText = []
        self.timeCharFin = None
        self.lives = []

        self.Qtable=np.zeros((5,595))
        
        #key events
        self.accept('escape', sys.exit)
        self.accept('q', self.menuToggle, ['display'])
        self.accept('e', self.menuToggle, ['remove'])
        self.accept('p', self.pause)
        
        #tasks
        if self.start:
            taskMgr.add(self.startScreen, 'start')
    
    def addTasks(self,task):
        self.circularRoad()
        self.inRoadWall()
        self.outRoadWall()
        self.makelogfail()
        self.displayLives()
        self.displayLaps()
        taskMgr.add(self.move, "move")
        taskMgr.add(self.moveSim, 'moveSim')
        taskMgr.add(self.countdown, 'countdown')
        taskMgr.add(self.mapPrev, 'map')
        taskMgr.add(self.takeLives, 'lives')
        taskMgr.add(self.moveCam, 'cam')
    
    def collideInit(self):
        mNode = CollisionNode('mario')
        mNode.addSolid(CollisionSphere(0,0,0,self.scale-2))
        marioCol = self.mario.attachNewNode(mNode)
        
        yNode = CollisionNode('yoshi')
        yNode.addSolid(CollisionSphere(0,0,0,self.scale-2))
        yoshiCol = self.yoshi.attachNewNode(yNode)
        
        return marioCol
    
    #コース作成
    def circularRoad(self):
        #geom format and data
        z = 15
        #points = self.vDataRows // 2 #one circle
        #x = rcos(t)
        #y = rsin(t)
        p=300
        t_incr = (2*math.pi) / p
        str = 5
        
        format = GeomVertexFormat.getV3n3c4t2()
        vData = GeomVertexData('cRoad', format, Geom.UHStatic)
        vData.setNumRows(18*self.vDataRows+4)
        vertex = GeomVertexWriter(vData, 'vertex')
        normal = GeomVertexWriter(vData, 'normal')
        color = GeomVertexWriter(vData, 'color')
        texcoord = GeomVertexWriter(vData, 'texcoord')
        
        #直線
        for i in range(p+1):
            x = i * str
            vertex.addData3f(x,0,z)
            vertex.addData3f(x,self.r_2-self.r_1,z)

            for n in range(2):
                normal.addData3f(x,self.r_2-self.r_1,z)
            
            #print(x)
            color.addData4f(0,1,1,1)
            color.addData4f(1,1,1,1)
            texcoord.addData2f(x,0)
            texcoord.addData2f(x,self.r_2-self.r_1)
            
        #曲線
        for i in range(150):
            angle = t_incr * i
            x_1 = self.r_1 * math.sin(angle)
            y_1 = self.r_1 * math.cos(angle+(t_incr*150))
            
            x_2 = self.r_2 * math.sin(angle)
            y_2 = self.r_2 * math.cos(angle+(t_incr*150))
            
            #print(y_2)
            vertex.addData3f(p*str+x_1, y_1+750, z)
            vertex.addData3f(p*str+x_2, y_2+750, z)

            for n in range(2):
                normal.addData3f(0,0,z)
            
            if i%2 == 0: #rainbow road
                color.addData4f(1,1,1,1)#白色
                color.addData4f(0,1,1,1)#水色
                color.addData4f(1,1,1,1)
                color.addData4f(0,1,1,1)
            
            texcoord.addData2f(x_1,y_1)
            texcoord.addData2f(x_2,y_2)

        #直線
        for i in range(p):
            x = i * str
            vertex.addData3f(p*str-x,1350,z)
            vertex.addData3f(p*str-x,1500,z)

            for n in range(2):
                normal.addData3f(p*str-x,self.r_2-self.r_1,z)
            
            #print(x)
            color.addData4f(1,1,1,1)
            color.addData4f(0,1,1,1)
            texcoord.addData2f(x,0)
            texcoord.addData2f(p*str-x,self.r_2-self.r_1)
        
        #曲線
        for i in range(151):
            angle = t_incr * i
            x_1 = self.r_1 * math.sin(-angle)
            y_1 = self.r_1 * math.cos(angle)
            
            x_2 = self.r_2 * math.sin(-angle)
            y_2 = self.r_2 * math.cos(angle)
            
            #print(x_1)
            vertex.addData3f(x_1, y_1+750, z)
            vertex.addData3f(x_2, y_2+750, z)

            for n in range(2):
                normal.addData3f(0,0,z)
            
            if i > 147:#finish line
                color.addData4f(1,0,0,1)#赤
                color.addData4f(1,0,0,1)#赤
            elif i%2 == 0: #rainbow road
                color.addData4f(1,1,1,1)#白色
                color.addData4f(0,1,1,1)#水色
                color.addData4f(1,1,1,1)
                color.addData4f(0,1,1,1)
            
            texcoord.addData2f(x_1,y_1)
            texcoord.addData2f(x_2,y_2)
        
        #geom primitives
        cRoad = GeomTristrips(Geom.UHStatic)
        cRoad.add_consecutive_vertices(0, 18*self.vDataRows+4)
        cRoad.close_primitive()
        
        #connect data and primitives
        cirGeom = Geom(vData)
        cirGeom.addPrimitive(cRoad)
        
        cirNode = GeomNode('geomNode')
        cirNode.addGeom(cirGeom)
        
        self.cirNodePath = render.attachNewNode(cirNode)
        self.cirNodePath.set_two_sided(True)
        
    #壁(内)
    def inRoadWall(self):
        z=15
        hight=10
        p=300
        t_incr = (2*math.pi) / p
        str = 5
        
        format = GeomVertexFormat.getV3n3c4t2()
        inData = GeomVertexData('cRoad', format, Geom.UHStatic)
        inData.setNumRows(18*self.vDataRows+4)
        vertex = GeomVertexWriter(inData, 'vertex')
        normal = GeomVertexWriter(inData, 'normal')
        color = GeomVertexWriter(inData, 'color')
        texcoord = GeomVertexWriter(inData, 'texcoord')
        
        #直線
        for i in range(p+1):
            x = i * str
            vertex.addData3f(x,self.r_2-self.r_1,z)
            vertex.addData3f(x,self.r_2-self.r_1,z+hight)
            for n in range(2):
                normal.addData3f(x,self.r_2-self.r_1,z)
                color.addData4f(0,1,0,1)
                texcoord.addData2f(x,0)
            
        #曲線
        for i in range(150):
            angle = t_incr * i
            x_1 = self.r_1 * math.sin(angle)
            y_1 = self.r_1 * math.cos(angle+(t_incr*150))
            vertex.addData3f(p*str+x_1, y_1+750, z)
            vertex.addData3f(p*str+x_1, y_1+750, z+hight)
            for n in range(2):
                normal.addData3f(0,0,z)
            if i%2 == 0:
                color.addData4f(0,1,0,1)#緑色
                color.addData4f(0,1,0,1)
                color.addData4f(0,1,0,1)
                color.addData4f(0,1,0,1)
            texcoord.addData2f(x_1,y_1)
            texcoord.addData2f(x_1,y_1)

        #直線
        for i in range(p):
            x = i * str
            vertex.addData3f(p*str-x,1350,z)
            vertex.addData3f(p*str-x,1350,z+hight)
            for n in range(2):
                normal.addData3f(p*str-x,self.r_2-self.r_1,z)
                color.addData4f(0,1,0,1)
                texcoord.addData2f(x,0)
        
        #曲線
        for i in range(151):
            angle = t_incr * i
            x_1 = self.r_1 * math.sin(-angle)
            y_1 = self.r_1 * math.cos(angle)
            vertex.addData3f(x_1, y_1+750, z)
            vertex.addData3f(x_1, y_1+750, z+hight)
            for n in range(2):
                normal.addData3f(0,0,z)
            if i%2 == 0:
                color.addData4f(0,1,0,1)#緑色
                color.addData4f(0,1,0,1)
                color.addData4f(0,1,0,1)
                color.addData4f(0,1,0,1)
            texcoord.addData2f(x_1,y_1)
            texcoord.addData2f(x_1,y_1)
  
        #geom primitives
        inRoad = GeomTristrips(Geom.UHStatic)
        inRoad.add_consecutive_vertices(0, 18*self.vDataRows+4)
        inRoad.close_primitive()
        
        #connect data and primitives
        incirGeom = Geom(inData)
        incirGeom.addPrimitive(inRoad)
        
        incirNode = GeomNode('geomNode')
        incirNode.addGeom(incirGeom)
        
        self.incirNodePath = render.attachNewNode(incirNode)
        self.incirNodePath.set_two_sided(True)
        
    #壁(外)
    def outRoadWall(self):
        z=15
        hight=10
        p=300
        t_incr = (2*math.pi) / p
        str = 5
        
        format = GeomVertexFormat.getV3n3c4t2()
        outData = GeomVertexData('cRoad', format, Geom.UHStatic)
        outData.setNumRows(18*self.vDataRows+4)
        vertex = GeomVertexWriter(outData, 'vertex')
        normal = GeomVertexWriter(outData, 'normal')
        color = GeomVertexWriter(outData, 'color')
        texcoord = GeomVertexWriter(outData, 'texcoord')
        
        #直線
        for i in range(p+1):
            x = i * str
            vertex.addData3f(x,0,z)
            vertex.addData3f(x,0,z+hight)

            for n in range(2):
                normal.addData3f(x,0,z)
                color.addData4f(0,1,0,1)
                texcoord.addData2f(x,0)            
        #曲線
        for i in range(150):
            angle = t_incr * i
            x_2 = self.r_2 * math.sin(angle)
            y_2 = self.r_2 * math.cos(angle+(t_incr*150))
            vertex.addData3f(p*str+x_2, y_2+750, z)
            vertex.addData3f(p*str+x_2, y_2+750, z+hight)

            for n in range(2):
                normal.addData3f(0,0,z)
            
            if i%2 == 0: #rainbow road
                color.addData4f(0,1,0,1)#緑色
                color.addData4f(0,1,0,1)
                color.addData4f(0,1,0,1)
                color.addData4f(0,1,0,1)
            
            texcoord.addData2f(x_2,y_2)
            texcoord.addData2f(x_2,y_2)

        #直線
        for i in range(p):
            x = i * str
            vertex.addData3f(p*str-x,1500,z)
            vertex.addData3f(p*str-x,1500,z+hight)

            for n in range(2):
                normal.addData3f(p*str-x,self.r_2-self.r_1,z)
                color.addData4f(0,1,0,1)
                texcoord.addData2f(p*str-x,self.r_2-self.r_1)
        
        #曲線
        for i in range(151):
            angle = t_incr * i
            x_2 = self.r_2 * math.sin(-angle)
            y_2 = self.r_2 * math.cos(angle)
           
            #print(x_1)
            vertex.addData3f(x_2, y_2+750, z)
            vertex.addData3f(x_2, y_2+750, z+hight)

            for n in range(2):
                normal.addData3f(0,0,z)
            
            if i%2 == 0: #rainbow road
                color.addData4f(0,1,0,1)#緑色
                color.addData4f(0,1,0,1)
                color.addData4f(0,1,0,1)
                color.addData4f(0,1,0,1)
            
            texcoord.addData2f(x_2,y_2)
            texcoord.addData2f(x_2,y_2)
        #geom primitives
        outRoad = GeomTristrips(Geom.UHStatic)
        outRoad.add_consecutive_vertices(0, 18*self.vDataRows+4)
        outRoad.close_primitive()
        
        #connect data and primitives
        outcirGeom = Geom(outData)
        outcirGeom.addPrimitive(outRoad)
        
        outcirNode = GeomNode('geomNode')
        outcirNode.addGeom(outcirGeom)
        
        self.outcirNodePath = render.attachNewNode(outcirNode)
        self.outcirNodePath.set_two_sided(True)
    
    #壁との衝突
    def checkWallCol(self):
        if (self.mario.getX() >= 0 and self.mario.getX() <= 1500):
            if self.mario.getY() <= 5 or (self.mario.getY() >= 145 and self.mario.getY() <= 1355) or self.mario.getY() >= 1495:
                self.collideWall()

    def collideWall(self):
        if self.mario.getH() <= 270 and self.mario.getH() >=90: mario_sign = 45
        else: mario_sign = 135
        self.mario.setH(mario_sign)
    
    #マリオとヨッシーの衝突
    def checkCharCol(self):
        if abs(self.yoshi.getX() - self.mario.getX()) < 10 and \
            abs(self.yoshi.getY() - self.mario.getY()) < 10 and \
            abs(self.yoshi.getZ() - self.mario.getZ()) < 10:
                self.collideYoshi()
    
    def collideYoshi(self):
        #altered use of conservation of momentum
        if self.mario.getH() != 0: mario_sign = self.mario.getH() / abs(self.mario.getH())
        else: mario_sign = 0
        if self.yoshi.getH() != 0: yoshi_sign = self.yoshi.getH() / abs(self.yoshi.getH())
        else: yoshi_sign = 0
        
        self.mario.setH(self.mario.getH() + mario_sign*15)
        self.yoshi.setH(self.yoshi.getH() - mario_sign*15)
     
        
    #コース場外判定
    def isOffRoad(self, player):
        if(player.getX()<=1500 and player.getX()>=0):
            return player.getY()<0 or (player.getY() > 150 and player.getY()<1350 ) or player.getY()>1500
        elif player.getX() > 1500 :
            distFromCen = distance(1500,750,player.getX(), player.getY())
            return distFromCen < 600 or distFromCen > 750
        else:
            distFromCen = distance(0,750,player.getX(), player.getY())
            return distFromCen < 600 or distFromCen > 750
    
    #ほとんどコース場外判定
    def almostOffRoad(self, player):
        #for computer player, detect when almost off the road
        if (player.getX()<=1500 and player.getX()>=0):
            outer = (player.getY()>0 and player.getY()<30)
            inner = (player.getY()<150 and player.getY()>120)
        elif player.getX() > 1500 :
            distFromCen = distance(1500,750,player.getX(), player.getY())
            inner = ( distFromCen > 600 and distFromCen < 630 )
            outer = ( distFromCen < 750 and distFromCen > 720 )
        else:
            distFromCen = distance(0,750,player.getX(), player.getY())
            inner = ( distFromCen > 600 and distFromCen < 630 )
            outer = ( distFromCen < 750 and distFromCen > 720 )
       
        return inner or outer
    
    #プレイヤの落下チェック
    def checkFellOff(self, player):
        #checks if the player fell off the road
        if self.isOffRoad(player) and not player.falling:
            player.numFellOff += 1
            player.startFallTime = globalClock.getFrameTime()
            player.startFallPos = player.getPos()
            if player == self.yoshi: self.yoshiStartH = self.yoshi.getH()
            player.falling = True
            #if player.numFellOff > 2:
                #if player == self.yoshi: player.gameover = True
                #if player == self.mario: self.gameOver()
    
    #ゴールラインのチェック
    def checkFinishLine(self,player):
        #checks if the player crossed the finish line
        if player.getX() >=1500: player.crossed = False
        if player.getX() <= 0 and (player.getY() >= 0 and player.getY() <=150 ) and player.getZ() >= 15 and not player.crossed:
            player.lap += 1
            player.crossed = True
            #print('player' : player,'Time' : player.raceTime,'周回数' : player.lap-1)
            
            '''#3周走ったときの処理
            if player.lap > 2: #final lap completed
                player.finishTime = roundtoThou(player.raceTime)
                
                if player == self.mario:
                    self.victory = True
                    if self.loss == False and self.mario.gameover == False:
                        vic = displayBigText('VICTORY!', (0.8, -1),  (255,255,0,1))
                        self.OSimageText.append(vic)
                        escText = displaySmallText('press esc to quit program', (0.8,-1.2),
                                                    (255,255,255,0.7))
                        self.OSimageText.append(escText)
                elif player == self.yoshi:
                    self.loss = True
                    escText = displaySmallText('press esc to quit program', (0.8,-1.2), (255,255,255,0.7))
                    self.OSimageText.append(escText)
                    if self.mario.gameover == False and self.victory == False:
                        compwins = displayBigText('COMPUTER WINS', (0.4, -1),  (255,0,0,0.5))
                        self.OSimageText.append(compwins)
            '''    

    def moveSim(self,task):
        
        dt = globalClock.getDt()
        self.timeDelay += dt
        
        h_speed = self.yoshi.h_speed
        y_speed = self.yoshi.y_speed
        z_speed = 10
        
        #コースから落ちそうなら角度調整ヨッシー (AI)
        if self.almostOffRoad(self.yoshi):
            distFromCen = distance(0,0,self.yoshi.getX(), self.yoshi.getY())
            if distFromCen > self.r_1 and distFromCen < self.r_1 + 30:
                h_speed += self.AIadjust
            elif distFromCen < self.r_2 and distFromCen > self.r_2 - 30:
                h_speed -= self.AIadjust
        
        #change position, angle
        dh = h_speed * dt
        dy = y_speed * dt
        dz = z_speed * dt
        if self.timeDelay > self.wait:
            self.yoshi.raceTime += dt
            self.yoshi.setH(self.yoshi.getH() + dh)
            self.yoshi.setY(self.yoshi, dy)
        
        #fell off road
        self.checkFellOff(self.yoshi)
                
        if self.yoshi.falling:
            self.yoshi.setZ(self.yoshi.getZ() - dz)
            self.yoshi.y_speed = 0
            self.resetPreFallPos(self.yoshi, self.yoshi.startFallPos)
        
        #crossed finish line
        self.checkFinishLine(self.yoshi)
        
        if self.yoshi.crossed: self.displayLaps(self.yoshi)
        
        return task.cont
    
    #マリオの操作
    def move(self, task):
        # print(self.cdMusic.status())
        if self.playing and self.playRaceMusic:
            self.rMusic.play()
            self.playing = False
        
        dt = globalClock.getDt()
        if not self.menuDisplayed:
            self.timeDelay += dt
        
        #方向キーでマリオを操作
        #enable moving mario with direction keys
        h_speed = self.mario.h_speed
        y_speed = self.mario.y_speed
        z_speed = 50
        x_speed = 0
        h_incr = 80
        y_incr = 0.2
        max_speed = -40
        min_speed = 100
        right_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.right())
        left_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.left())
        forward_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.up())
        backward_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.down())
        #d_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey(b"d"))
        #f_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey(b"f"))

        if right_down:
            h_speed -= h_incr
        if left_down:
            h_speed += h_incr

        if forward_down:
            if y_speed <= max_speed: self.mario.y_speed = max_speed
            else: self.mario.y_speed = y_speed - y_incr
        else: 
            if y_speed < 0:self.mario.y_speed = y_speed + y_incr

        if backward_down:
            if y_speed >= min_speed: self.mario.y_speed = min_speed
            else: self.mario.y_speed = y_speed + 5 * y_incr
        #if d_down and self.timeDelay > self.wait:
        #    self.drifted = True
        #    self.mario.lookAt(self.center)
        #    self.mario.setH(self.mario.getH() + 180)
        #    x_speed -= y_incr * (4/3)
        #if f_down and self.timeDelay > self.wait:
        #    self.drifted = True
        #    self.mario.lookAt(self.center)
        #    self.mario.setH(self.mario.getH() + 180)
        #    x_speed += y_incr * (4/3)
        #if not d_down and not f_down and self.drifted and self.timeDelay > self.wait:
        #    self.drifted = False
        #    self.mario.setH(self.mario.getH() + 90)
        
        #change position, angle
        dh = h_speed * dt
        dy = y_speed * dt 
        dz = z_speed * dt
        dx = x_speed * dt
        if self.timeDelay > self.wait:
            self.mario.raceTime += dt
            self.mario.setH(self.mario.getH() + dh)
            self.mario.setY(self.mario, dy)
            self.mario.setX(self.mario, dx)
        
        #mario and yoshi collision
        self.checkCharCol()
        #self.checkWallCol()
        
        #fell off road
        self.checkFellOff(self.mario)
                
        if self.mario.falling:
            self.mario.setZ(self.mario.getZ() - dz)
            self.mario.y_speed = 0
            self.resetPreFallPos(self.mario, self.mario.startFallPos)
        
        #crossed finish line
        self.checkFinishLine(self.mario)
        
        if self.mario.crossed: self.displayLaps(self.mario)
        
        #show leaderboard if someone completed 3 laps or gameover
        if ( self.mario.gameover or self.victory or self.loss ) and self.charFin:
            self.timeCharFin = globalClock.getFrameTime()
            self.charFin = False
        
        if self.timeCharFin != None and globalClock.getFrameTime() > self.timeCharFin + self.wait/2:
            self.leaderboard()
        
        #マリオのログデータを更新
        X = (self.mario.getX()+800) // 10
        Y = (self.mario.getY()+50) // 10
        num = X+Y*310
        path = 'C:\\Users\\RYOUGO\\.conda\\envs\\kankyou02\\112-tp-final-master\\log.txt'
        with open(path) as f:
            lines = f.readlines()
        line = lines[int(num)]

        NUM,A,B,R,L,reward= line.split(',',6)
        NUM = int(NUM) + 1
        if forward_down==True: A = int(A)+1
        if backward_down==True: B = int(B)+1
        if right_down==True: R = int(R)+1
        if left_down==True: L = int(L)+1
        if self.mario.falling == True: reward = -1
        else: reward = int(reward)+ 0.0002
        
        #行を指定してtxtに書き込む
        line =int(NUM),int(A),int(B),int(R),int(L),float(reward)
        print(type(line))
        #print(num)
        lines[int(num)] = str(line)+'\n'
        
        with open(path,mode="w")as f:
            f.writelines(lines)
        
        return task.cont
    
    #ログファイルの作成・初期化
    def makelogfail(self):
        path = 'C:\\Users\\RYOUGO\\.conda\\envs\\kankyou02\\112-tp-final-master\\log.txt'
        f = open(path,'w')
        for i in range(49600):
            f.write('0,0,0,0,0,0\n')
        f.close()
        
    #カメラのアングル操作        
    def moveCam(self, task):

        dt = globalClock.getDt()
        
        #enable camera spinning around mario using a,s,w,x,k,l keys
        cam = 0
        camSpeed = 700
        vert = 0
        hor = 0
        a_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey(b"a"))
        s_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey(b"s"))
        
        
        if a_down:
            cam += camSpeed
        if s_down:
            cam -= camSpeed
        
        dCam = cam * dt
        self.camera.setX(self.camera, dCam)
        
        #keep camera close to mario, from roaming ralph:
        #https://github.com/panda3d/panda3d/tree/master/samples/roaming-ralph
        camVector = self.mario.getPos() - self.camera.getPos()
        camVector.setZ(0) #don't change camera's z distance
        camDist = camVector.length() #magnitude
        camVector.normalize() #unit vector (direction)
        
        if camDist > self.camMaxDist:
            self.camera.setPos(self.camera.getPos() + \
                                camVector * (camDist - self.camMaxDist))
            camDist = self.camMaxDist
        if camDist < self.camMinDist:
            self.camera.setPos(self.camera.getPos() - \
                                camVector * (self.camMinDist - camDist))
            camDist = self.camMinDist
        
        if self.camera.getZ() != self.mario.getZ() + 6.0:
            self.camera.setZ(self.mario.getZ() + 6.0)
        
        self.camera.setH(self.mario.getH())
        self.camera.setZ(self.mario.getZ()+25)
        
        self.camera.lookAt(self.floater)
        
        return task.cont
    
    #落下後プレイヤをコースに戻す
    def resetPreFallPos(self, player, pos):
        #place player back on the road
        
        if player.startFallTime != None and not player.gameover and globalClock.getFrameTime() > player.startFallTime + self.wait/4:
            player.falling = False
            
            if (player.getX() >= 0 and player.getX() <= 1500):
                if player.getY() <= 750:adjustY=50
                else: adjustY=1400
            else:
                if player.getX() > 1500:
                    adjustX = 1500
                    adjustY = 50
                else:
                    adjustX = 0
                    adjustY = 1400

            player.setPos(adjustX, adjustY, 15)
            if player == self.mario: self.mario.y_speed = 0
            elif player == self.yoshi:
                self.yoshi.y_speed = 0
                self.yoshi.setPos(1500,100,15)
        
    #各プレイヤのラップ数を表示する
    def displayLaps(self, player=None):
        #display the lap number each player is on
        
        #past finish line
        if player != None and player.getX() >-10  and player.getY() < 150 and \
            player.getY() > 0 and player.getZ() >= 15:
            player.crossed = False
        
        #前のラップ数を破棄
        if self.mario_lapText != None: self.mario_lapText.destroy()
        if self.yoshi_lapText != None: self.yoshi_lapText.destroy()
        
        #新しいラップ数
        self.mario_lapText = OnscreenText(text = 'Lap: ' + str(self.mario.lap), fg = (255,0,0,1), 
                                        scale =  0.05, parent=base.a2dTopLeft, pos=(2.5,-0.15), 
                                        align=TextNode.ALeft)
        self.yoshi_lapText = OnscreenText(text = 'Lap: ' + str(self.yoshi.lap), fg = (0,255,0,1), 
                                        scale =  0.05, parent=base.a2dTopLeft, pos=(2.5,-0.25), 
                                        align=TextNode.ALeft)
        self.OSimageText.append(self.mario_lapText)
        self.OSimageText.append(self.yoshi_lapText)
    
    #プレイヤのライフを表示
    def displayLives(self):
        #display the number of lives user player has left
        
        livesText = displaySmallText('lives:', (0.1,-0.15), (255,255,255,1))
        self.OSimageText.append(livesText)
        #images made in preview
        self.life1 = OnscreenImage(image = 'images/life.png', pos = (-0.9,0,0.87), scale = 0.03)
        self.life2 = OnscreenImage(image = 'images/life.png', pos = (-0.8,0,0.87), scale = 0.03)
        self.life3 = OnscreenImage(image = 'images/life.png', pos = (-0.7,0,0.87), scale = 0.03)
        self.OSimageText.append(self.life1)
        self.OSimageText.append(self.life2)
        self.OSimageText.append(self.life3)
    
    def takeLives(self, task):
        if self.mario.numFellOff == 1: self.life3.destroy()
        if self.mario.numFellOff == 2: self.life2.destroy()
        if self.mario.numFellOff == 3: self.life1.destroy()
        
        return task.cont
    
    #円形トラックに対するプレイヤの角度の取得
    def getPlayerAngle(self, player):
        #get player's current angle wrt the circular track
        x = player.getX()
        y = player.getY()
        
        if x == 0:
            if y<=0: angle = 90
            else: angle = -90
        else: angle = math.degrees(math.atan(abs(y)/abs(x)))
        
        if y<=0 and x<=0: pass #Q1
        elif y<0 and x>0: angle = 180 - angle #Q2
        elif y>0 and x<0: angle = -angle #Q3
        elif y>0 and x>0: angle = -180 + angle #Q4
        
        return angle
    
    def mapPrev(self,task):
        #show map in corner with all player's positions
        
        radius = 0.085
        mapX = 1
        mapY = 0.8
        #image made in preview
        mapP = OnscreenImage(image = 'images/map.png', pos = (mapX,0,mapY), scale = 0.1)
        self.OSimageText.append(mapP)
        
        marioAngle = self.getPlayerAngle(self.mario)
        marioX = mapX + radius*math.cos(math.radians(marioAngle))
        marioY = mapY + radius*math.sin(math.radians(marioAngle))
        
        yoshiAngle = self.getPlayerAngle(self.yoshi)
        yoshiX = mapX + radius*math.cos(math.radians(yoshiAngle))
        yoshiY = mapY + radius*math.sin(math.radians(yoshiAngle))
        
        finishX = mapX + radius*math.cos(math.radians(180))
        finishY = mapY + radius*math.sin(math.radians(180))
        
        #images made in preview
        marioSym = OnscreenImage(image = 'images/mariosym.png', 
                                pos = (marioX,0,marioY), scale = 0.01)
        yoshiSym = OnscreenImage(image = 'images/yoshisym.png', 
                                pos = (yoshiX,0,yoshiY), scale = 0.01)
        finishSym = OnscreenImage(image = 'images/finishsym.png', 
                                pos = (finishX,0,finishY), scale = 0.01)
        
        self.OSimageText.append(marioSym)
        self.OSimageText.append(yoshiSym)
        self.OSimageText.append(finishSym)
        
        return task.cont
    
    def startScreen(self, task):
        if self.escapeStart: return
        
        if self.start:
            #image from supermariorun.com
            logo = OnscreenImage(image = 'images/mario.png', pos = (0.01,0,-0.5), scale = 0.3)
            
            welcome = OnscreenText('Welcome to Mario Kart!', fg = (255,0,0,1), scale = 0.2,
                                    shadow = (255,255,255,1), parent = base.a2dTopLeft, 
                                    pos = (0.2, -0.5), align = TextNode.ALeft)
            
            show_menu = OnscreenText('press Q to see key instructions', fg = (255,255,255,1), 
                                    scale = 0.1, shadow = (0,255,0,1), 
                                    parent = base.a2dTopLeft, pos = (0.6, -0.8), 
                                    align = TextNode.ALeft)
            
            start_game = OnscreenText('press space to start game!', fg = (255,255,255,1), 
                                    scale = 0.1, shadow = (0,0,255,1), 
                                    parent = base.a2dTopLeft, pos = (0.7, -1), 
                                    align = TextNode.ALeft)
            
            self.startText.append(logo)
            self.startText.append(welcome)
            self.startText.append(show_menu)
            self.startText.append(start_game)
        
        q_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey(b"q"))
        space_down = base.mouseWatcherNode.isButtonDown(KeyboardButton.space())
        
        if q_down: self.menuStart = True
        if q_down or space_down:
            self.start = False
            self.escapeStart = True
            for text in self.startText: text.destroy()
        if space_down: 
            self.addTasks(task)
            
        return task.cont
        
    
    def countdown(self, task):
        #display countdown before game starts
        #print(taskMgr)
        taskMgr.remove('start')
        
        dt = globalClock.getDt()
        # print(dt)
        if not self.menuDisplayed:
            self.timeDelay += dt
        interval = self.wait/3
        
        #countdown sound effect
        if self.counting:
            self.cdMusic.play()
            self.counting = False
        
        if self.timeDelay < interval*1:
            # print(self.timeDelay, interval*1)
            display = displayBigText('3', (1.3,-1), (255,255,255,1), (255,0,0,1))
            self.countdowns.append(display)
        elif self.timeDelay < interval*2:
            # print(self.timeDelay, interval*2)
            for display in self.countdowns: display.destroy()
            display = displayBigText('2', (1.3,-1), (255,255,255,1), (255,255,0,1))
            self.countdowns.append(display)
        elif self.timeDelay < interval*3:
            # print(self.timeDelay, interval*3)
            for display in self.countdowns: display.destroy()
            display = displayBigText('1', (1.3,-1), (255,255,255,1), (0,255,0,1))
            self.countdowns.append(display)
        elif self.timeDelay < interval*4:
            # print(self.timeDelay, interval*4)
            for display in self.countdowns: display.destroy()
            display = displayBigText('GO!', (1.1,-1), (255,255,255,1))
            self.countdowns.append(display)
        elif self.timeDelay > interval*4:
            for display in self.countdowns: display.destroy()
            self.playRaceMusic = True
        
        return task.cont
        
    def pause(self, fromFunction = None):
        self.paused = not self.paused
            
        if self.paused == True:
            if fromFunction == None: #not from menu
                displayPause = displayBigText('PAUSED', (0.85, -1),  (255,255,255,1))
                self.isPaused.append(displayPause)
                self.OSimageText.append(displayPause)
            
            self.addMove -= 1
            taskMgr.remove("move")
            taskMgr.remove("moveSim")
            taskMgr.remove("countdown")
            
        else: #unpause
            if fromFunction == None: 
                for item in self.isPaused: item.destroy()
            
            if self.addMove > 0: return
            self.addMove += 1
            taskMgr.add(self.move, "move")
            taskMgr.add(self.moveSim, "moveSim")
            taskMgr.add(self.countdown, 'countdown')
            
    def menuToggle(self, keyInput):
        #display menu of key instructions
        
        taskMgr.remove('start')
        for text in self.startText: text.destroy()
        
        #pause countdown music if playing
        if self.cdMusic.status() == self.cdMusic.PLAYING:
            self.cdMusicTime = self.cdMusic.getTime()
            self.cdMusic.setPlayRate(0)
        
        yIncr = -0.1
        directions = [ 'esc: quit program', 'Q: view menu', 'E: escape menu', 
                        'P: pause/unpause', 'Up/Down: move Mario forward/backward',
                        "Right/Left: change Mario's direction", 'A/S: rotate camera',
                        'D/F: drift Mario forwards/backwards', 
                        "during drift, use Up/Down in place of Right/Left" ]
        
        if keyInput == 'display':
            self.menuDisplayed = True
            self.menuCount += 1
            if self.menuCount > 1: return
            
            self.paused = False
            self.pause('menu')
           
            title = displaySmallText('Mario Kart Key Legend', (0.75,-0.1), 
                                    (255,255,255,1), (0,0,0,1))
            self.OSimageText.append(title)
            
            self.lines = [ title ]
            
            for i in range(2,len(directions)+2):
                y = yIncr*i
                
                line = displaySmallText(directions[i-2], (0.1,y), (255,255,255,0.75), 
                                        (0,0,0,1))
                self.lines.append(line)
                self.OSimageText.append(line)
            
            #access menu from start screen
            if self.menuStart:
                line = displaySmallText('press E to start game!', (0.8,-1.5), 
                                        (255,255,0,1), (0,0,0,1)) 
                self.lines.append(line)
                self.OSimageText.append(line)  
                self.menuStart = False
                  
        if keyInput == 'remove':
            self.menuDisplayed = False
            #escape menu
            self.menuCount = 0
            self.paused = True
            self.pause('menu')
            for line in self.lines:
                line.destroy()
            
            self.circularRoad()
            self.inRoadWall()
            self.outRoadWall()
            self.makelogfail()
            self.displayLives()
            self.displayLaps()
            # taskMgr.add(self.moveSim, 'moveSim')
            # taskMgr.add(self.countdown, 'countdown')
            # taskMgr.add(self.move, "move")
            taskMgr.add(self.mapPrev, 'map')
            taskMgr.add(self.takeLives, 'lives')
            taskMgr.add(self.moveCam, 'cam')
        
    def gameOver(self):
        self.mario.gameover = True
        if self.victory == False and self.loss == False:
            gameText = displayBigText('GAME OVER', (0.65, -1),  (255,255,255,1))
            self.OSimageText.append(gameText)
            escText = displaySmallText('press esc to quit program', (0.8,-1.2), (255,255,255,0.7))
            self.OSimageText.append(escText)
        
    def leaderboard(self):
        #remove everything else on the screen
        taskMgr.remove('moveSim')
        taskMgr.remove("move")
        taskMgr.remove('map')
        for child in render.getChildren():
            child.removeNode()
        for item in self.OSimageText:
            item.destroy()
        
        leaderB = displayBigText('LEADERBOARD', (0.45, -0.3), (255,255,0,1))
        firstPlace = displaySmallText('1st:', (0.5, -0.5), (255,255,0,1))
        secondPlace = displaySmallText('2nd:', (0.5, -0.6), (255,255,0,1))
        
        #characters that didn't finish
        if self.mario.finishTime == 0:
            self.mario.finishTime = roundtoThou(self.mario.raceTime)
        if self.yoshi.finishTime == 0:
            self.yoshi.finishTime = roundtoThou(self.yoshi.raceTime)
        
        if self.mario.finishTime <= self.yoshi.finishTime:
            marioY = -0.5
            yoshiY = -0.6
        else:
            marioY = -0.6
            yoshiY = -0.5
        
        marioRight = displaySmallText('Mario (User)', (0.8, marioY), (255,255,0,1))
        marioLeft = displaySmallText(str(self.mario.finishTime), (1.8, marioY), (255,255,0,1))
        yoshiRight = displaySmallText('Yoshi (Computer)', (0.8, yoshiY), (255,255,0,1))
        marioLeft = displaySmallText(str(self.yoshi.finishTime), (1.8, yoshiY), (255,255,0,1))
        escText = displaySmallText('press esc to quit program', (0.7,-1.8), (255,255,255,0.7))
        
        #image from https://mariokart.fandom.com/wiki/Mario
        image = OnscreenImage(image = 'images/leaderboardmario.png', pos = (0.01,0,-0.2), scale = 0.4)
        
game = Game()
game.run()
