ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-paho-mqtt py3-pyserial

COPY src/ /serial2mqtt

COPY run.sh /
RUN chmod +x /run.sh

CMD [ "/run.sh" ]