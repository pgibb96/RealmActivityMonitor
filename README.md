This Repo contains 2 packages.

## RealmActivityMonitor

This packages contains the lambda handler that fulfills the following purpose:

- Scrapes realmeye.com for last seen data
- Compares it previous last seen data stored in the dynamoDB store
- If there is new activity, sends one of several discord messages.

It's true purpose is to keep me from engaging in degenerative gaming.

## RealmActivtyMonitorCDK

### This package handles configuration of two stacks

- Lambda stack
- DynamoDB stack
