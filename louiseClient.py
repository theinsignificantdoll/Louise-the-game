from paho.mqtt import client as mclient
import random


class Hand:
    def __init__(self, playername=f"player{random.randint(10000, 99999)}", broker=None, port=None,
                 announce=print, externalserver=True, password=None, username=None):
        self.playername = playername
        self.externalserver = externalserver
        self.client = mclient.Client(playername)
        self.client.on_connect = self.on_connect
        self.password = password
        self.username = username

        if broker is not None:
            self.broker = broker
        elif self.externalserver:
            self.broker = "89.239.193.104"
            self.port = 10232
        else:
            self.broker = "192.168.3.41"
            self.port = 1883
        if port is not None:
            self.port = port
        if self.externalserver:
            if self.password is None or self.username is None:
                raise Exception("(password OR username IS None) AND externalserver IS True: CLASS Hand.__init__")
            self.client.username_pw_set(self.username, self.password)

        self.client.connect(broker, port)
        self.announce = announce
        self.subscribe()
        self.updatefunc = None
        self.timeleftfunc = None
        self.finished = False
        self.placement = -1
        self.gameprogress = ""

        self.registerself()

        self.cardhand = []
        self.opencards = []
        self.hiddencards = []
        self.requestcardhand()
        self.requestopencards()
        self.requesthiddencards()

    def registerself(self):
        self.client.publish("RegisterPlayer", self.playername)

    def requestcardhand(self):
        self.client.publish(self.playername, "Get/CardHand")

    def requestopencards(self):
        self.client.publish(self.playername, "Get/OpenCards")

    def requesthiddencards(self):
        self.client.publish(self.playername, "Get/HiddenCards")

    def requeststart(self):
        self.client.publish(self.playername, "StartMatch")

    def replace(self, handInd, cardsInd):
        self.client.publish(self.playername, f"Replace,{handInd},{cardsInd}")

    def update(self, mess=""):
        if self.updatefunc is not None:
            self.updatefunc(mess)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        if topic != "Timeleft":
            self.update(topic)
        if topic == "Announcements":
            self.announce(payload)
        elif topic == "Timeleft":
            self.dotimeleft(payload)
        elif topic == "Leaderboard":
            print(payload)
        elif topic == "GameProgress":
            self.gameprogress = payload
        elif topic == f"placementRecv{self.playername}":
            print(payload)
            self.finished = True
            self.placement = int(payload.split("-")[0])+1
        elif topic == f"HandRecv{self.playername}":
            if not payload:
                self.cardhand = []
                return
            self.cardhand = [int(n_) for n_ in payload.split(",")]
        elif topic == f"OpenRecv{self.playername}":
            if not payload:
                self.opencards = []
                return
            self.opencards = [int(n_) for n_ in payload.split(",")]
        elif topic == f"HiddenRecv{self.playername}":
            if not payload:
                self.hiddencards = []
                return
            self.hiddencards = [int(n_) for n_ in payload.split(",")]

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    def subscribe(self):
        self.client.subscribe("Announcements")
        self.client.subscribe("Leaderboard")
        self.client.subscribe("GameProgress")
        self.client.subscribe("Timeleft")
        self.client.subscribe(f"placementRecv{self.playername}")
        print(f"HandRecv{self.playername}")
        self.client.subscribe(f"HandRecv{self.playername}")
        self.client.subscribe(f"OpenRecv{self.playername}")
        self.client.subscribe(f"HiddenRecv{self.playername}")
        self.client.on_message = self.on_message

    def get_points(self):
        p = sum(self.opencards) + sum(self.hiddencards)
        return p

    def dopass(self):
        self.client.publish(self.playername, "Do/Pass")

    def dotimeleft(self, seconds=0):
        if self.timeleftfunc is not None:
            self.timeleftfunc(seconds)

