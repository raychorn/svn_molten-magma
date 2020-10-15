#this migrate class is used for creating new database schema from
#SF. The table name is prepended with 'sf' Account in SF is sf_acoount in MySQL.
#The datatype is also preserved(String, datetime and int) in the local database.

class Sfadmin < ActiveRecord::Migration

    @acctdesc=Account.connection.get_entity_def("Account")
    @attcol=@acctdesc.columns 
    
    @userdesc=User.connection.get_entity_def("User")
    @usrcol=@userdesc.columns   
    
    @ssldesc=SelfServiceUser.connection.get_entity_def("SelfServiceUser")
    @sslcol=@ssldesc.columns   
    
    @casedesc=Case.connection.get_entity_def("Case")
    @casecol=@casedesc.columns   
    
    @contdesc=Contact.connection.get_entity_def("Contact")
    @contcol=@contdesc.columns     
    
    @soldesc=Solution.connection.get_entity_def("Solution")
    @solcol=@soldesc.columns    
    
    @attchdesc=Attachment.connection.get_entity_def("Attachment")
    @attachcol=@attchdesc.columns    
    
  
  def self.up
     create_table "sfaccount", :force => true do |t|      
          @attcol.each do |val|
            @api=val.api_name
            @cols=val.name
            @type=val.type            
            @datatype=""
            
            #case field_type
              #when /int/i
                #:integer
              #when /currency|percent/i
                #:float
             # when /datetime/i
               # :datetime
              #when /date/i
               # :date
              #when /id|string|textarea/i
                #:text
              #when /phone|fax|email|url/i
                #:string
              #when /blob|binary/i
                #:binary
              #when /boolean/i
                #:boolean
              #when /picklist/i
                #:text
             # when /reference/i
               # :text
            #end
                        
            if (@type.to_s().downcase()=="text"|| @type.to_s().downcase()=="string")              
              @datatype="string"                                                  
            elsif (@type.to_s().downcase()=="datetime")
              @datatype="datetime"
            elsif(@type.to_s().downcase()=="date")
              @datatype="date"   
            elsif(@type.to_s().downcase()=="integer")
              @datatype="int"
            elsif(@type.to_s().downcase()=="float")
              @datatype="float"             
              #@datatype="string"
            else
              @datatype="string"                           
            end            
            
            if @api!="Id"
               #puts @datatype
               #if @api="Type"
                  #t.column "sf_type", :string, :null => false                
               
               t.column "#{@cols}", :"#{@datatype}"                           
            end               
        end 
        t.column "sf_id", :string, :null => false      
     end
     
     create_table "sfuser", :force => true do |t|      
          @usrcol.each do |val|
            @api=val.api_name
            @cols=val.name
            @type=val.type            
            @datatype=""           
            
                        
            if (@type.to_s().downcase()=="text"|| @type.to_s().downcase()=="string")              
              @datatype="string"                                                  
            elsif (@type.to_s().downcase()=="datetime")
              @datatype="datetime"
            elsif(@type.to_s().downcase()=="date")
              @datatype="date"   
            elsif(@type.to_s().downcase()=="integer")
              @datatype="int"
            elsif(@type.to_s().downcase()=="float")
              @datatype="float"             
              #@datatype="string"
            else
              @datatype="string"                           
            end              
            
            if @api!="Id"
               #puts @datatype
               #if @api="Type"
                  #t.column "sf_type", :string, :null => false                
               
               t.column "#{@cols}", :"#{@datatype}"                           
            end             
        end 
        t.column "sf_id", :string, :null => false      
     end
     
     create_table "sfssl", :force => true do |t|      
          @sslcol.each do |val|
            @api=val.api_name
            @cols=val.name
            @type=val.type            
            @datatype=""
                                  
           if (@type.to_s().downcase()=="text"|| @type.to_s().downcase()=="string")              
              @datatype="string"                                                  
            elsif (@type.to_s().downcase()=="datetime")
              @datatype="datetime"
            elsif(@type.to_s().downcase()=="date")
              @datatype="date"   
            elsif(@type.to_s().downcase()=="integer")
              @datatype="int"
            elsif(@type.to_s().downcase()=="float")
              @datatype="float"             
              #@datatype="string"
            else
              @datatype="string"                           
            end              
            
            if @api!="Id"
               #puts @datatype
               #if @api="Type"
                  #t.column "sf_type", :string, :null => false                
               
               t.column "#{@cols}", :"#{@datatype}"                           
            end              
        end 
        t.column "sf_id", :string, :null => false      
     end
     
     create_table "sfcase", :force => true do |t|      
          @casecol.each do |val|
            @api=val.api_name
            @cols=val.name
            @type=val.type            
            @datatype=""
           
                                   
            if (@type.to_s().downcase()=="text"|| @type.to_s().downcase()=="string")              
              @datatype="string"                                                  
            elsif (@type.to_s().downcase()=="datetime")
              @datatype="datetime"
            elsif(@type.to_s().downcase()=="date")
              @datatype="date"   
            elsif(@type.to_s().downcase()=="integer")
              @datatype="int"
            elsif(@type.to_s().downcase()=="float")
              @datatype="float"             
              #@datatype="string"
            else
              @datatype="string"                           
            end             
            
           if @api!="Id"
               #puts @datatype
               #if @api="Type"
                  #t.column "sf_type", :string, :null => false                
               
               t.column "#{@cols}", :"#{@datatype}"                        
            end          
        end 
        t.column "sf_id", :string, :null => false      
     end
     
     create_table "sfcontact", :force => true do |t|      
          @contcol.each do |val|
            @api=val.api_name
            @cols=val.name
            @type=val.type            
            @datatype=""
                                  
            if (@type.to_s().downcase()=="text"|| @type.to_s().downcase()=="string")              
              @datatype="string"                                                  
            elsif (@type.to_s().downcase()=="datetime")
              @datatype="datetime"
            elsif(@type.to_s().downcase()=="date")
              @datatype="date"   
            elsif(@type.to_s().downcase()=="integer")
              @datatype="int"
            elsif(@type.to_s().downcase()=="float")
              @datatype="float"             
              #@datatype="string"
            else
              @datatype="string"                           
            end              
            
                       
            if @api!="Id"
               #puts @datatype
               #if @api="Type"
                  #t.column "sf_type", :string, :null => false                
               
               t.column "#{@cols}", :"#{@datatype}"                          
            end         
        end 
        t.column "sf_id", :string, :null => false      
     end
     
     create_table "sfsolution", :force => true do |t|      
          @solcol.each do |val|
            @api=val.api_name
            @cols=val.name
            @type=val.type            
            @datatype=""
                                  
            if (@type.to_s().downcase()=="text"|| @type.to_s().downcase()=="string")              
              @datatype="string"                                                  
            elsif (@type.to_s().downcase()=="datetime")
              @datatype="datetime"
            elsif(@type.to_s().downcase()=="date")
              @datatype="date"   
            elsif(@type.to_s().downcase()=="integer")
              @datatype="int"
            elsif(@type.to_s().downcase()=="float")
              @datatype="float"             
              #@datatype="string"
            else
              @datatype="string"                           
            end                
            
                       
            if @api!="Id"
               #puts @datatype
               #if @api="Type"
                  #t.column "sf_type", :string, :null => false                
               
               t.column "#{@cols}", :"#{@datatype}"                           
            end         
        end 
        t.column "sf_id", :string, :null => false      
     end
     
     create_table "sfattach", :force => true do |t|      
          @attachcol.each do |val|
            @api=val.api_name
            @cols=val.name
            @type=val.type            
            @datatype=""
                                  
            if (@type.to_s().downcase()=="text"|| @type.to_s().downcase()=="string")              
              @datatype="string"                                                  
            elsif (@type.to_s().downcase()=="datetime")
              @datatype="datetime"
            elsif(@type.to_s().downcase()=="date")
              @datatype="date"   
            elsif(@type.to_s().downcase()=="integer")
              @datatype="int"
            elsif(@type.to_s().downcase()=="float")
              @datatype="float"             
              #@datatype="string"
            else
              @datatype="string"                           
            end               
            
                       
            if @api!="Id"
               #puts @datatype
               #if @api="Type"
                  #t.column "sf_type", :string, :null => false                
               
               t.column "#{@cols}", :"#{@datatype}"                           
            end         
        end 
        t.column "sf_id", :string, :null => false      
     end
     
   end

   def self.down
     drop_table "sfaccount"
     drop_table "sfuser"
     drop_table "sfssl"
     drop_table "sfcase"
     drop_table "sfcontact"
     drop_table "sfsolution"
     drop_table "sfattach"
   end
end
