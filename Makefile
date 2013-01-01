.PHONY:	clean
clean:
	rm -f MANIFEST
	rm -rf dist build
	find . -name "*~" -exec rm -rf {} \;

