# Classes that use the SalesForce database should be 
# subclasses of SalesforceRecord.
# 
# Defines a ClassMethod called +clone_class+. This method
# takes a single parameter, which is the name of the cloned class. 
# When called, this makes the instance method +save_and_clone+ available. 
# #save_and_clone saves this record and clone in the local database.
class SalesforceRecord < ActiveRecord::Base
    self.abstract_class = true
    self.establish_connection :salesforce
    
    @@clone_options = nil
        
    def cloned_class
      AppConstants::CLASS_MAPPINGS[self.class.to_s].constantize
    end

    def self.clone_options
      @@clone_options
    end

    def save_and_clone
      raise("Cloned class not defined via #cloned_class") unless cloned_class
      logger.info("Saving ASF record #{self.class} and getting ready to clone to #{self.cloned_class}")
      if save
        # clone_to_local
        record = SalesforceSync.insert_record(self.class.column_names,self.class.find(self.id),self.class,cloned_class)
        return record
      else
        self
      end
    end
    
    def save_and_update
      raise("Cloned class not defined via #cloned_class") unless cloned_class
      logger.info("Saving ASF record #{self.class} and getting ready to update to #{self.cloned_class}")
      if save
        record = SalesforceSync.update_record(self,cloned_class.find_by_sf_id(id),self.class,cloned_class)
        return record
      end
    end
    
    def clone_exists?
      cloned_class.find_by_sf_id(id)
    end
    alias clone clone_exists?

    def clone_to_local
      klass = cloned_class
      logger.info("Cloning #{self.class} record to #{klass} with attributes: #{attributes}")
      current_time = Time.now
      local = klass.new(attributes.merge({:created_date => current_time,
                                          :system_modstamp => current_time})) 
      local.save
      ActiveRecord::Base.connection.execute("update #{klass.table_name} set sf_id = '#{id}' where id='#{local.id}'")
      return local
    end
end # SalesforceRecord

