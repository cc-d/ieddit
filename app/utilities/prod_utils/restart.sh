if ! screen -list | grep -q "myscreen"; then
	screen -S website -p 0 -X quit
fi


cd /home/ccarterdev/i2/ieddit/app/ 
screen -S website python3 run.py 8000
