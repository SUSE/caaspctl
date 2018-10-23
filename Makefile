MAIN_RUNNER = "from caasp.__main__ import main ; main()"

dist-clean:
	rm -rf build dist __main__.py

dist-zip: dist-clean
	# hack for creating "executable" zips for Python
	@echo $(MAIN_RUNNER) > __main__.py
	python setup.py bdist --format=zip
	@rm -rf build *.egg-info __main__.py
	@echo ">>> Created a ZIP archive that can be 'run' with python in the 'dist' directory..."

dist-rpm: dist-clean
	python setup.py bdist --format=rpm
	@rm -rf build *.egg-info
	@echo ">>> Created a RPM package in the 'dist' directory..."


