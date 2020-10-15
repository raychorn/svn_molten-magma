# Filters added to this controller will be run for all controllers in the application.
# Likewise, all the methods added will be available for all controllers.
class ApplicationController < ActionController::Base
  @BATCH_SIZE=50

 def insert_account
      puts "Updating Account Object .........."
      begin 
        @sfcol=Account.columns
        @sqlcol=Sfaccount.columns
        @sfaccts=Account.find(:all, :limit => 3000) 
      rescue => e  
        logger.error(e)        
        puts "Error in Querying Account data: ", $!, "\n"
        print "ERROR IN Querying Account data:"+e                                
      end
                      
      @sfaccts.each do |sfa|                       
        tempHash = Hash.new()
        @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfaccount.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")      
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"         
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                 
        
          begin   
            if(@id !=nil)   
              sqlUpdate=Sfaccount.find(@id)
              sqlUpdate.update_attributes(tempHash)
              sqlUpdate.save
            else      
              sacct=Sfaccount.new(tempHash)
              sacct.save
              @msg="Succesfully Inserted the records....."
            end
          rescue => e
            logger.error(e)
            id=tempHash["sf_id"]
            puts "Error in inserting data: ", $!, "\n"
            print "ERROR IN INSERTING DATA:"+e              
            updateErrorTable(e,"Account","Sfaccount",id) 
            sendEmail(e)                     
         end  
      end            
      return @msg
    end 
  
    def insert_case
        puts "Updating Case Object .........."
        begin        
          @sfcol=Case.columns
          @sqlcol=Sfcase.columns
          @sfaccts=Case.find(:all, :condition =>"record_type_id='01230000000001XAAQ'",:limit => 15000) 
          #start new change
#          @sfaccts=[]
#          @allcont=Sfcontact.find_all	   
#          @queryLen1=(@allcont.length).to_i
#          puts "Number of Contact records that need to be inserted are #{@queryLen1}"       
#  	      @allcont.each do |cont|
#  	    	@contid=cont.sf_id
#  	    	@eachcase=Case.find(:all, :conditions => "contact_id = '#{@contid}'")
#  	    	@eachcase.each do |icases|
#  	    		@sfaccts << icases
#  	    	end
#  	      end	 
		  #end new change 
          
          #@sfaccts=Case.find_by_sql("select * from Case where createdDate < 2004-01-01T00:00:00Z limit 5000")
          @queryLen=(@sfaccts.length).to_i
          puts "Number of Cases records that need to be inserted are #{@queryLen}"
          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Case data: ", $!, "\n"
          print "ERROR IN Querying Case data:"+e                       
          #sendEmail(e) 
        end    
        @sfaccts.each do |sfa|                           
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfcase.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")      
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end              
              
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfcase.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else         
                sacct=Sfcase.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING CASE RECORD:"+e              
              updateErrorTable(e,"Case","Sfcase",id) 
              sendEmail(e)                     
          end  
        end            
        return @msg
      end 
      
      def insert_user
        puts "Updating User Object .........."
        begin
          @sfcol=User.columns
          @sqlcol=Sfuser.columns
          @sfusers=User.find(:all, :limit => 1000)  
        rescue => e  
          logger.error(e)        
          puts "Error in Querying User data: ", $!, "\n"
          print "ERROR IN Querying User data:"+e                                  
        end   
          
        @sfusers.each do |sfa|           
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfuser.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")      
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end   
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfuser.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else    
                sacct=Sfuser.new(tempHash)              
                sacct.save
              end
              
              @msg="Succesfully Inserted the records....."
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING DATA:"+e              
              updateErrorTable(e,"User","Sfuser",id) 
              sendEmail(e)                     
          end                
            
        end            
        return @msg
      end 
      
      
      def insert_ssl
        puts "Updating Self Service User Object .........."
        begin
          @sfcol=SelfServiceUser.columns
          @sqlcol=Sfssl.columns
          @sfssl=SelfServiceUser.find(:all, :limit => 4000)
        rescue => e  
          logger.error(e)        
          puts "Error in Querying SSL data: ", $!, "\n"
          print "ERROR IN Querying SSL data:"+e                       
          
        end     
        
        @sfssl.each do |sfa|               
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfssl.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")      
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfssl.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else                  
                sacct=Sfssl.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING CASE RECORD:"+e              
              updateErrorTable(e,"SelfServiceUser","Sfssl",id) 
              sendEmail(e)                  
          end               
            
        end            
        return @msg
      end 
      
      def insert_contact
        puts "Updating Contact Object .........."
        begin
          @sfcol=Contact.columns
          @sqlcol=Sfcontact.columns
          @sfcont=Contact.find(:all, :limit => 17000)    
          #@sfcont=Contact.find(:all, :conditions => "account_id = '00130000000ODT9AAO' or account_id = '00130000000M4oKAAS' or account_id = '00130000004hcgiAAA' or account_id = '001300000019kKMAAY'" ,:limit => 2000)
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Contact data: ", $!, "\n"
          print "ERROR IN Querying Contact data:"+e                       
          
        end   
        
        @sfcont.each do |sfa|                                  
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfcontact.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")                  
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfcontact.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else               
                sacct=Sfcontact.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING CASE RECORD:"+e              
              updateErrorTable(e,"Contact","Sfcontact",id) 
              sendEmail(e)                            
          end            
           
        end            
        return @msg
      end 
      
      def insert_solution
        puts "Updating Solution Object .........."        
        begin
          @sfcol=Solution.columns
          @sqlcol=Sfsolution.columns
          @sfsol=Solution.find(:all, :limit => 3600)
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Solution data: ", $!, "\n"
          print "ERROR IN Querying Solution data:"+e                                 
        end      
        
        @sfsol.each do |sfa|                        
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfsolution.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")                  
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfsolution.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else                 
                sacct=Sfsolution.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING CASE RECORD:"+e              
              updateErrorTable(e,"Solution","Sfsolution",id) 
              sendEmail(e) 
          end   
        end         
        return @msg
      end 
      
      def insert_attachment
        puts "Updating Attachemnt .........."
        begin
          @sfcol=Attachment.columns
          @sqlcol=Sfattach.columns
          @sfatt=Attachment.find(:all, :limit => 10000)  
          
          #start new change
#          @sfatt=[]
#          @allcont=Sfcase.find_all	   
#          @queryLen1=(@allcont.length).to_i
#          puts "Number of Case records that need to be inserted are #{@queryLen1}"       
#  	      @allcont.each do |cs|
#  	    	@contid=cs.sf_id
#  	    	@eachcase=Attachment.find(:all, :conditions => "parent_id = '#{@contid}'",:limit => 10000)
#  	    	@eachcase.each do |icases|
#  	    		@sfatt << icases
#  	    	end
#  	      end	
#  	      
#  	      @queryLen=(@sfatt.length).to_i
#          puts "Number of Attachment records that need to be inserted are #{@queryLen}"
#           
		  #end new change 
		  
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Attachment data: ", $!, "\n"
          print "ERROR IN Querying Attachment data:"+e                                 
        end   
        
        @sfatt.each do |sfa|                  
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfattach.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")      
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfattach.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else               
                sacct=Sfattach.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
            logger.error(e)
            id=tempHash["sf_id"]
            puts "Error in inserting data: ", $!, "\n"
            print "ERROR IN INSERTING CASE RECORD:"+e              
            updateErrorTable(e,"Attachment","Sfattach",id) 
            sendEmail(e) 
          end    
        end            
        return @msg
      end 
      
      def insert_case_comments
        puts "Updating Case Commnets .........."
        begin
          @sfcol=CaseComment.columns
          @sqlcol=Sfccomment.columns
          @sfatt=CaseComment.find(:all, :limit => 70000)  
          #@queryLen=(@sfatt.length).to_i
          #puts "Number of cc records that need to be inserted are #{@queryLen}"
          
          #start new change
#          @sfatt=[]
#          @allcont=Sfcase.find_all	   
#          @queryLen1=(@allcont.length).to_i
#          puts "Number of Case records that need to be inserted are #{@queryLen1}"       
#  	      @allcont.each do |cs|
#  	    	@contid=cs.sf_id
#  	    	@eachcase=CaseComment.find(:all, :conditions => "parent_id = '#{@contid}'",:limit => 10000)
#  	    	@eachcase.each do |icases|
#  	    		@sfatt << icases
#  	    	end
#  	      end	
#  	      
#  	      @queryLen=(@sfatt.length).to_i
#          puts "Number of cc records that need to be inserted are #{@queryLen}"
#           
		  #end new change 
		  #
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Case Comment data: ", $!, "\n"
          print "ERROR IN Querying Case Comment data:"+e                                 
        end   
        
        @sfatt.each do |sfa|                  
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfccomment.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name                   
            @value=sfa.send("#{@field}")      
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfccomment.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else               
                sacct=Sfccomment.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
            logger.error(e)
            id=tempHash["sf_id"]
            puts "Error in inserting data: ", $!, "\n"
            print "ERROR IN INSERTING CASE RECORD:"+e              
            updateErrorTable(e,"CaseComment","Sfccomment",id) 
            sendEmail(e) 
          end    
        end            
        return @msg
      end 
      
      def insert_category_data
        puts "Updating Category Data .........."
        begin
          @sfcol=CategoryData.columns
          @sqlcol=Sfcatdata.columns
          @sfcat=CategoryData.find(:all , :limit =>5000)
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Case Comment data: ", $!, "\n"
          print "ERROR IN Querying Case Comment data:"+e                                  
        end   
        
        @sfcat.each do |sfa|                  
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfcatdata.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")      
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfcatdata.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else               
                sacct=Sfcatdata.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
            logger.error(e)
            id=tempHash["sf_id"]
            puts "Error in inserting data: ", $!, "\n"
            print "ERROR IN INSERTING CATEGORY DATA RECORD:"+e              
            updateErrorTable(e,"CategoryData","Sfcatdata",id) 
            sendEmail(e) 
          end    
        end            
        return @msg
      end 
      
      def insert_category_node
        puts "Updating Category Node .........."
        begin
          @sfcol=CategoryNode.columns
          @sqlcol=Sfcatnode.columns
          @sfatt=CategoryNode.find(:all, :limit =>1000)            
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Category Node data: ", $!, "\n"
          print "ERROR IN Querying CaseCategory Node data:"+e                                  
        end   
        
        @sfatt.each do |sfa|                  
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfcatnode.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name             
            @value=sfa.send("#{@field}")      
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              if(@field.to_s().downcase()=="type")
                @value=sfa[:type]
                @field="sf_type"                
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfcatnode.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else               
                sacct=Sfcatnode.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
            logger.error(e)
            id=tempHash["sf_id"]
            puts "Error in inserting data: ", $!, "\n"
            print "ERROR IN INSERTING CASE RECORD:"+e              
            updateErrorTable(e,"CategoryNode","Sfcatnode",id) 
            sendEmail(e) 
          end    
        end            
        return @msg
      end 
            
      def updateErrorTable(errormsg,entity,sqlent,id)
          errorHash=Hash.new()
          if(errormsg !=nil)            
            errorHash["error_message"]=errormsg
            errorHash["sf_id"]=id
            errorHash["sf_entity"]=entity
            errorHash["sql_entity"]=sqlent
            serr=Error.new(errorHash)
            serr.save
          end        
      end
      
      def sendEmail(msg)
        msg = [ "Subject: MySQL database error\n", "\n", msg ]
        Net::SMTP.start('rye.moltenmagma.com') do |smtp|        
          smtp.sendmail( msg,  'ramya@molten-magma.com', ['ramya@molten-magma.com'] )
        end
      end
      
      def updateError()
        puts "Updating Error Object .........."                
        @sfcol=Error.columns
        @sfsol=Error.find(:all, :limit => 50)   
        @sfsol.each do |sfa|                           
          @id=sfa.id
          @sfid=sfa.sf_id
          @sfent=sfa.sf_entity.to_s()
          @sqlent=sfa.sql_entity                   
          @entCol=eval("#{@sfent}").columns
          
          @sfRec=eval("#{@sfent}").find(:first, :conditions => "id = '#{@sfid}'")
          
            tempHash = Hash.new()
            @entCol.each do |acol|
              @field=acol.name                               
              @value=@sfRec.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                  @value=sfa[:type]
                  @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end 
           
          begin         
              sacct=eval("#{@sqlent}").new(tempHash)
              sacct.save
              @msg="Succesfully Inserted the records....."
              Error.delete(@id)
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING DATA:"+e              
              updateErrorTable(e,"User","Sfuser",id) 
              sendEmail(e)                     
          end    
        end            
        return @msg
      end  
      
      
      
      def sync_account
        puts "Updating last modified Account Object .........."
        begin
          @sfcol=Account.columns
          @sqlcol=Sfaccount.columns
          @lastRec=Sfaccount.find(:first, :order => "last_modified_date DESC")         
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)       
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now          
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedAcct=Account.connection.get_updated("Account", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedAcct.length).to_i          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Account data: ", $!, "\n"
          print "ERROR IN Querying Account data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedAcct !=nil
          @sfUpdatedAcct.each do |sfu|              
            ids=sfu
            sfa=Account.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfaccount.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name               
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfaccount.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfaccount.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Account","Sfaccount",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      def sync_case
        puts "Updating last modified Case Object .........."
        begin
          @sfcol=Case.columns
          @sqlcol=Sfcase.columns          
          @lastRec=Sfcase.find(:first, :order => "last_modified_date DESC")
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)            
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now          
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedcase=Case.connection.get_updated("Case", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedcase.length).to_i          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Account data: ", $!, "\n"
          print "ERROR IN Querying Account data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedcase !=nil
          @sfUpdatedcase.each do |sfu|              
            ids=sfu
            sfa=Case.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfcase.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name               
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfcase.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfcase.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Case","Sfcase",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      
      def sync_user
        puts "Updating last modified User Object .........."
        begin
          @sfcol=User.columns
          @sqlcol=Sfuser.columns          
          @lastRec=Sfuser.find(:first, :order => "last_modified_date DESC")
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)            
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now          
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedUsers.length).to_i          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying User data: ", $!, "\n"
          print "ERROR IN Querying User data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedUsers !=nil
          @sfUpdatedUsers.each do |sfu|              
            ids=sfu
            sfa=User.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfuser.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfuser.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfuser.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"User","Sfuser",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      def sync_ssl
        puts "Updating last modified Case Object .........."
        begin
          @sfcol=SelfServiceUser.columns
          @sqlcol=Sfssl.columns          
          @lastRec=Sfssl.find(:first, :order => "last_modified_date DESC")
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)          
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now          
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedssl=SelfServiceUser.find_by_sql("select Id from SelfServiceUser where LastModifiedDate > #{@fromdate}")
          @queryLen=(@sfUpdatedssl.length).to_i          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying SelfServiceUser data: ", $!, "\n"
          print "ERROR IN Querying SelfServiceUser data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedssl !=nil
          @sfUpdatedssl.each do |sfu|             
            ids=sfu.id
            sfa=SelfServiceUser.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfssl.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name               
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfssl.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfssl.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"SelfServiceUser","Sfssl",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      
      def sync_contact
        puts "Updating last modified Case Object .........."
        begin
          @sfcol=Contact.columns
          @sqlcol=Sfcontact.columns
          @lastRec=Sfcontact.find(:first, :order => "last_modified_date DESC")          
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)         
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end  
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now          
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedcont=Contact.connection.get_updated("Contact", "2006-07-25T17:27:28Z}", "#{@todate}")
          @queryLen=(@sfUpdatedcont.length).to_i          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Contact data: ", $!, "\n"
          print "ERROR IN Querying Contact data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedcont !=nil
          @sfUpdatedcont.each do |sfu|  
            ids=sfu
            sfa=Contact.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfcontact.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name               
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfcontact.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfcontact.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Contact","Sfcontact",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      def sync_solution
        puts "Updating last modified Solution Object .........."
        begin
          @sfcol=Solution.columns
          @sqlcol=Sfsolution.columns
          @lastRec=Sfsolution.find(:first, :order => "last_modified_date DESC")          
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)            
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now          
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedsol=Solution.connection.get_updated("Solution", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedsol.length).to_i          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Solution data: ", $!, "\n"
          print "ERROR IN Querying Solution data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedsol !=nil
          @sfUpdatedsol.each do |sfu|              
            ids=sfu
            sfa=Solution.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfsolution.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name               
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfsolution.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfsolution.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Solution","Sfsolution",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      def sync_attachment
        puts "Updating last modified Attachment Object .........."
        begin
          @sfcol=Attachment.columns
          @sqlcol=Sfattach.columns          
          @lastRec=Sfattach.find(:first, :order => "last_modified_date DESC")
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)            
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now          
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedattach=Attachment.connection.get_updated("Attachment", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedattach.length).to_i
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Attachment data: ", $!, "\n"
          print "ERROR IN Querying Attachment data:"+e                                 
        end   
        if @sfUpdatedattach !=nil
          @sfUpdatedattach.each do |sfu|              
            ids=sfu
            sfa=Attachment.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfattach.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfattach.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfattach.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Attachment","Sfattach",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      def sync_case_comments
        puts "Updating last modified Case Comment Object .........."
        begin
          @sfcol=CaseComment.columns
          @sqlcol=Sfccomment.columns          
          @lastRec=Sfccomment.find(:first, :order => "created_date DESC")
          if(@lastRec!=nil)
            @ldate=@lastRec.created_date-(60*60)    
                   
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now          
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedattach=CaseComment.connection.get_updated("CaseComment", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedattach.length).to_i          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Case Comment data: ", $!, "\n"
          print "ERROR IN Querying Case Comment data:"+e                                 
        end   
        if @sfUpdatedattach !=nil
          @sfUpdatedattach.each do |sfu|  
            ids=sfu
            sfa=CaseComment.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfccomment.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name               
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfccomment.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfccomment.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"CaseComment","Sfccomment",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      def sync_category_data
        puts "Updating last modified Category Data .........."
        begin
          @sfcol=CategoryData.columns
          @sqlcol=Sfcatdata.columns          
          @lastRec=Sfcatdata.find(:first, :order => "last_modified_date DESC")
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)           
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now         
          @currentTime=@currentTime.gmtime+(5*30)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedAcct=CategoryData.find_by_sql("select Id from CategoryData where LastModifiedDate > #{@fromdate}")
          @queryLen=(@sfUpdatedAcct.length).to_i         
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Category data: ", $!, "\n"
          print "ERROR IN Querying Category data:"+e                                 
        end   
        if @sfUpdatedAcct !=nil
          @sfUpdatedAcct.each do |sfu|              
            ids=sfu.id
            sfa=CategoryData.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfcatdata.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfcatdata.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfcatdata.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"CategoryData","Sfcatdata",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      def sync_category_node
        puts "Updating last modified Category Node Object .........."
        begin
          @sfcol=CategoryNode.columns
          @sqlcol=Sfcatnode.columns
          @lastRec=Sfcatnode.find(:first, :order => "last_modified_date DESC")
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date-(15*60)                        
          else
            @deflast=Time.now
            @deflast=@deflast.gmtime
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now                    
          @currentTime=@currentTime.gmtime+(5*30)
          @diff=@currentTime-@ldate
          @days=(@diff)/60*60*24          
          if(@days >30)
            @deflast=Time.now
            @ldate=@deflast-(11*60*60*60)
            @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ")
          end          
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ")           
          @sfUpdatedAcct=CategoryNode.find_by_sql("select Id from CategoryNode where LastModifiedDate > #{@fromdate}")
          @queryLen=(@sfUpdatedAcct.length).to_i          
          
        rescue => e  
          logger.error(e)           
          puts "Error in Querying Account data: ", $!, "\n"
          print "ERROR IN Querying Account data:"+e                                 
        end   
        if @sfUpdatedAcct !=nil
          @sfUpdatedAcct.each do |sfu|              
            ids=sfu.id
            sfa=Account.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfcatnode.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              @value=sfa.send("#{@field}")      
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                if(@field.to_s().downcase()=="type")
                    @value=sfa[:type]
                    @field="sf_type"                
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfcatnode.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfcatnode.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"CategoryNode","Sfcatnode",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
        
end