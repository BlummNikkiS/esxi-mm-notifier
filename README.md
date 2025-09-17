# esxi-mm-notifier
A simple program to receive Telegram notifications about which ESXi hosts enter maintenance mode and which leave it.

Run from folder with docker file:

1) Change the values ​​of the variables in the config.ini file to your own.
2) docker build -t esxi-mm-notifier .
3) docker run --restart always --name esxi-mm-notifier esxi-mm-notifier
