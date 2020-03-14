% zimfarm(1)
% Jens Korte and other
% 2020-03-14

# Name
zimfarm - the zimfarm worker manager script to manage the build process of zim files hosted at <https://kiwix.org>

# Synopsis
zimfarm  \<command> [option]

# Description

With this script you can start/stop the worker and the manager, list the containers, read logs, remove all docker containers/images/volums and update the script itself.

zimfarm is provided for your comfort only. A Zimfarm worker is just a Docker container spawning other containers that download recipes (instructions) and build the zim file.  If you like to control everything, you can run it manually setting the appropriate options. Otherwise, use our handy bash script.

# Commands

## starting, stopping, restarting the manager and the worker

* **start** or **restart**: (re)start pulls a new version of the Docker image and also reapplies the configuration. The worker is not restarted, the task is not canceled and the work for the actual zim file is not lost.  
* **stop manager**: stops the manager without stopping the currently running workers. A stopped manager doesn't receive new task to do. The running task(s) is/are completed and uploaded but your worker is not listed any more at <https://farm.openzim.org/workers>.  
* **stop \<task-name\>** stops a task and its dependencies (scraper, dnscache). Marks it as canceled. Can take a minute.  
* **shutdown**: stops the manager and all the running tasks. Use this to stop the worker completely. Running tasks will be marked as canceled. Can take a couple minutes.

## gathering information

* **ps [parameters]**: displays a list of running containers with Zimfarm labels. Optionnal: pass parameter to ps (-a, -nX).  
* **logs \<name\> [n]**: displays logs. \<name\> can be 'manager' or a task. n is an optionnal lines number (default: 100).  
* **inspect \<name\>**: inspect details of the 'manager' or container.  
* **config**: show the config file path and the search paths.  

## housekeeping
* **update**: displays a command you could use update this very script.  
* **update do**: attempt to run the `zimfarm update` command.  
* **prune**: removes unused containers and volumes to save space. You can put that in a daily cron task.  

# See also
* config file: zimfarm.config (search path: /usr/local/bin/zimfarm.config:./.zimfarm.config:./zimfarm.config:/etc/zimfarm.config)  
* website: <https://github.com/openzim/zimfarm/>  
* overview and stats on the workers and recipes: <https://farm.openzim.org/>  
* available zim files: <https://wiki.kiwix.org/wiki/Content_in_all_languages>  
