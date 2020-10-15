class Rating < ActiveRecord::Base
  set_primary_key "id"
  
  #------------------
  # CONSTANTS
  #------------------
  
  # attributes that are non-vote counting
  EXCLUDE_FROM_COUNT = [:id, :sfsolution_id].freeze
  
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :sfsolution
  
  #------------------
  # INSTANCE METHODS
  #------------------
  def total_votes
    count_attributes.values.inject(0)  { |sum, count| sum + count }
  end
  
  # Returns a hash of attribute => value of all attributes contain vote counts.
  def count_attributes
    count = attributes
    EXCLUDE_FROM_COUNT.each { |exclude| count.delete(exclude.to_s) }
    count
  end
end
