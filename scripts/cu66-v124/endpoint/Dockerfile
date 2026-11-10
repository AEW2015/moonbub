FROM gamebub-native-endpoint-base:20261109
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libboost1.83-dev && rm -rf /var/lib/apt/lists/*
USER 1000:1000
