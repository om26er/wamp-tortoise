clean:
	rm db.*

deps:
	pip install -r requirements.txt

start:
	python3 -u main.py
