import time
import sys

def main():
    if len(sys.argv) != 2:
        print(f"Insufficient arguments\n\n Usage: python3 {sys.argv[1]} \"(MESSAGE)\"")
        sys.exit()
    else:
        message = sys.argv[1]
    print(f" IN DUMMY... You sent:{message}")
    count = 0
    while(True):
        if count == 20: 
            break
        time.sleep(1)
        count +=1
        print(f'Count: {count} {message}')

if __name__=="__main__":
    main()
