class CreateCountries < ActiveRecord::Migration
  def self.up
    create_table :country do |t|

      t.timestamps
    end
  end

  def self.down
    drop_table :country
  end
end
