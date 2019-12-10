# Celo Validator Monitor Discord Bot

unfriendly :robot:

This bot send an alert to Discord channel when
- (1) your validator does not produce a block for last 30 minutes.
- (2) your validator resumed and produced blocks for last 30 minutes.
- (3) Celo network does not produce blocks for 5 minutes.
- (4) Celo network resumed and produce blocks again.

We use 30 mins for validator and 5 mins for Celo network in Baklava testnet.
You can edit code to change above time intervals :)

## Install

```shell
$ python3 -m pip install -U discord.py
$ chmod +x discord_bot.py
$ # in a configuration setting file such as ~/.bash_profile
$ export CELO_VALIDATOR_NAME="Stark Industries"
$ export CELO_VALIDATOR_SIGNER_ADDRESS="0x3...0"
$ export CELO_MONITOR_DISCORD_BOT_TOKEN="A...A"
$ export CELO_MONITOR_DISCORD_CHANNEL="my celo channel name"
```

## Run

```shell
$ nohup ./discord_bot.py &
```
## Alert message

When your validator does not produce blocks for last 30 minutes.
- ![Validator ALERT](https://raw.githubusercontent.com/dsrvlabs/celo-validator-monitoring/master/img/celo-monitoring-alert1.png)

When your validator resumed and produced blocks for last 30 minutes.
- ![Validator OK](https://raw.githubusercontent.com/dsrvlabs/celo-validator-monitoring/master/img/celo-monitoring-alert2.png)

When Celo network does not produce blocks for 5 minutes.
```
[Chain stopped] Celo network has been stopped last 5 minutes.
```

When Celo network resumed and produce blocks again.
```
[Chain stopped] Celo network has been stopped, too.
```

