pep8:
	pep8 -r context.py --ignore=E501,E202,E225,E201,E241,E221
	pep8 -r contextview.py --ignore=E501,E202,E225,E201,E241,E221
	pep8 -r launcher --ignore=E501,E202,E225,E201,E241,E221

build-ext:
	python setup.py build_ext --inplace
