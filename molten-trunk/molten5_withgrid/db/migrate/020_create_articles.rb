class CreateArticles < ActiveRecord::Migration
  def self.up
    create_table :article do |t|
      t.column :title, :string
      t.column :body, :text
      t.column :created_at, :datetime
      t.column :updated_at, :datetime
    end
  end

  def self.down
    drop_table :article
  end
end
