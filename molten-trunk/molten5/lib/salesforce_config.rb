#!/usr/bin/env ruby

class SalesforceConfig
  attr_accessor :filename, :d_yaml
  def initialize()
    @filename = File.join(::RAILS_ROOT, 'config', 'database.yml')
    @d_yaml = YAML::load(ERB.new(IO.read(@filename)).result)
  end  
     
  def username
    @d_yaml['salesforce']['username']
  end  

  def password
    @d_yaml['salesforce']['password']
  end  
end


