# this run_job wrapper uses lockfiles to ensure that jobs do not run at the same
# times -- this wraps script/runner to ensure files are only running once and not
# concurrently
require 'lockfile'

# $lockfile_dir = "/var/lock" # better would be: "/var/lock" on most linux systems
#$lockfile_dir = "." # better would be: "/var/lock" on most linux systems
$lockfile_dir = "/var/www/apps/molten/shared/locks" # better would be: "/var/lock" on most linux systems

if __FILE__ == $0
  if ARGV.size <= 0
    puts "Usage: #$0 job_name"
    exit(1)
  end

  opts = { # :debug     => true,   # uncomment to debug
	   :retries   => 0,      # don't retry, if a job is running
	   :max_age   => 3600    # any lock files over an hour, just clear 
         } 

  lockfile = Lockfile.new "#{$lockfile_dir}/ruby_#{ARGV[0]}.lock", opts
  
  if lockfile.validlock?
    exit(1)
  end 

  begin
    lockfile.lock
   #  puts "ruby #{File.dirname(__FILE__) + "/../script/runner -e production '#{ARGV[0]}'" }"
    `ruby #{File.dirname(__FILE__) + "/../script/runner '#{ARGV[0]}' -e production" }`
  ensure
    lockfile.unlock
  end

end
