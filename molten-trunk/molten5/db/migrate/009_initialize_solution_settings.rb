class InitializeSolutionSettings < ActiveRecord::Migration
  def self.up
    Sfsolution.find(:all).each do |s| 
      begin
        s.save
      rescue
        say "Error updating solution [#{s.name}, #{s.id}]"
      end
    end
  end

  def self.down
    SfsolutionSetting.destroy_all
  end
end
