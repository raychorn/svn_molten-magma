load "rubyscript2exe"
require "rubyscript2exe"

if RUBYSCRIPT2EXE.is_compiling?
  begin
    d = Dir.entries("..")
  rescue
    d = []
  end

  RUBYSCRIPT2EXE.bin = []

  d.each { |item| RUBYSCRIPT2EXE.bin.push("../"+item) if ( (item != ".") && (item != "..") ) }
end

print "RUBYSCRIPT2EXE.bin.inspect=", RUBYSCRIPT2EXE.bin.inspect + "\n"

print "RUBYSCRIPT2EXE.is_compiling?=(#{RUBYSCRIPT2EXE.is_compiling?})\n"

print "RUBYSCRIPT2EXE.is_compiled?=(#{RUBYSCRIPT2EXE.is_compiled?})\n"

if RUBYSCRIPT2EXE.is_compiled?
  print "Current Dir is '#{Dir.getwd()}'."
  
  cmd = 'run-DEMO.cmd'
  print "cmd=(#{cmd})"

  begin
    exec(cmd)
  rescue
    print "Cannot run the DEMO."
  end
end

