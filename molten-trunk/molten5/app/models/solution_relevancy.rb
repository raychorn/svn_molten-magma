class SolutionRelevancy < ActiveRecord::Base
  set_primary_key "id"
  #------------------
  # VALIDATIONS
  #------------------
  validates_presence_of :rating_value_one, :rating_value_two, :rating_value_three,
                        :rating_value_four, :view_value, :update_value

  #------------------
  # CLASS METHODS
  #------------------  
  
  # Sends missing methods to the first record. 
  def self.method_missing(meth, *args, &block)
     if self.new.respond_to?(meth)
       raise "The relevancy setting does not exist for solutions. Please create it." unless rel = find(:first)
       rel.send(meth)
     else
       super
     end
  end
end
