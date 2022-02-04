FROM python:3.8

COPY dist/*.whl /
RUN pip3 install /*.whl
CMD ["bash"]
