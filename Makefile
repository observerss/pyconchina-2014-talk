all:
	invoke build
	invoke dist
	rm -rf pyconchina2014.jingchao
	cp -r dist pyconchina2014.jingchao
	zip -r pycon2014china.jingchao.zip pyconchina2014.jingchao
