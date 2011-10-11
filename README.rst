Mr.Rubber - your elastic friend
-------------------------------

Mr.Rubber is a supervisord event listener. When rubber is started it will dertmine how many processes
to keep running based on its settings and by detecting the number of cores on the system. It will
start or stop processes which match a spec to match the nominated process count.

Options are:

--programs (-p):
  Spec for which program names to control. Glob syntax such as "instance*" is supported.

--num (-n):
  The number of processes to run. Defaults to "auto" which will set this to the number of cpu cores detected
  when rubber first starts

--offset (-o):
  A number to modify the --num argument by. For instance if --num=auto and --offset=-2 and the detected cores was
  4 then the number of processes set to run would be 2.

For example if you are using buildout with supervisor you could do the following ::

    [supervisor]
    recipe=collective.recipe.supervisor
    plugins =
      mr.rubber
    programs =
      11 instance1 ${buildout:directory}/bin/instance1 [console] ${instance1:location} true
      12 instance2 ${buildout:directory}/bin/instance2 [console] ${instance2:location} true
      13 instance3 ${buildout:directory}/bin/instance3 [console] ${instance3:location} true
      14 instance4 ${buildout:directory}/bin/instance4 [console] ${instance4:location} true
    eventlisteners =
      rubber SUPERVISOR_STATE_CHANGE_RUNNING ${buildout:bin-directory}/rubber [-p instance* -o 0 -n auto]

History
-------

1.0 (11-10-11)
==============

- Initial working version released



