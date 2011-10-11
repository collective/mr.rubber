Mr.Rubber - your elastic friend
-------------------------------

Mr.Rubber is a supervisord event listener. When rubber is started it will dertmine how many processes
to keep running based on its settings and by detecting the number of cores on the system. It will
start or stop processes which match a spec to match the nominated process count.

Options are:

--programs (-p):
  Spec for which program names to control.

--num (-n):
  The number of processes to run. Defaults to "auto" which will set this to the number of cpu cores detected
  when rubber first starts

--offset (-o):
  A number to modify the --num argument by. For instance if --num=auto and --offset=-2 and the detected cores was
  4 then the number of processes set to run would be 2.

  


