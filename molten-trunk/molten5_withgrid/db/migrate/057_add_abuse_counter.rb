class AddAbuseCounter < ActiveRecord::Migration
    # old beast migration
  def self.up
    # execute "ALTER TABLE beast_#{RAILS_ENV}.post ADD abuse_counter int(11) default 0"
  end

  def self.down
    # execute "ALTER TABLE beast_#{RAILS_ENV}.post DROP abuse_counter"
  end
end
