import socket, os, time

def checkInternet(host="1.1.1.1", port=53, timeout=3):
    """
    Host: 1.1.1.1 (cloudflare dns)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        print("ERR: Couldn't connect to wifi, trying bluetooth tethering")
        try:
            os.system("bluetoothctl connect %s" % Secrets.deviceid)
            time.sleep(1.0)
            os.system("busctl call org.bluez /org/bluez/hci0/dev_%s org.bluez.Network1 Connect s nap" % Secrets.deviceid)
            time.sleep(0.5)
            os.system("sudo dhclient -v bnep0")
            time.sleep(0.5)
            return False
        except:
            print("Couldn't create Bluetooth tether")
            return False

if __name__ == "__main__":
    print(checkInternet())