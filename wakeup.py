import urllib.request
import time
   
def main():
	with urllib.request.urlopen('https://rrmob-ms-server.herokuapp.com') as response:
	   html = response.read()
	time.sleep(60)
	
if __name__ == "__main__":
    main()