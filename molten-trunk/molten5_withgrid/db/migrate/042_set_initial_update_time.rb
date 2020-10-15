class SetInitialUpdateTime < ActiveRecord::Migration
  def self.up
    Sfcase.find(:all).each do |c|
      c.set_update_time!
    end
  end

  def self.down
  end
end
