docker run -d \
-it \
--name ieddit \
-p 3000:80 \
--mount src="$(pwd)"/static,target=/usr/src/app/static,type=bind,readonly \
--mount src="$(pwd)"/templates,target=/usr/src/app/templates,type=bind,readonly \
ieddit:latest