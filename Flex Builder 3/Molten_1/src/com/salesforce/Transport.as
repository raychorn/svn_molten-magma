/*
Copyright (c) 2007 salesforce.com, inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
package com.salesforce
{
import com.salesforce.events.SendEvent;

import flash.events.EventDispatcher;
import flash.system.ApplicationDomain;

import mx.rpc.AsyncToken;
import mx.rpc.IResponder;
import mx.rpc.events.FaultEvent;
import mx.rpc.events.ResultEvent;
import mx.rpc.http.HTTPService;

[Event(name="sendRequest", type="com.salesforce.events.SendEvent")]
/**
 * 
 * @private
 * 
 */	
public class Transport extends EventDispatcher
{
  
  public var url:String;
  private var connection:HTTPService;
  

  public function Transport(url:String=null)
  {
    if (url != null)
    {
      this.url = url;
    }
  }
  
  private function newConnection():void
  { 
    connection = new HTTPService();
  }

  	public function send(envelope:XmlWriter,responder:IResponder, remote:Object = null):void
  	{
    	newConnection();
    	connection.method = "POST";
    	connection.url = url;
    	connection.contentType = "text/xml; charset=UTF-8";
    	
    	/*
    	 * append the flag to ensure Apex API will return errors under the 200 OK status rather than 500 normally specified for faults
		 * otherwise fault bodies are hidden from Flex 
		 * add user agent to allow tracking 
		 * UPDATE -- Cannot set the user header when runnning a flex app from a browser.  
		 * 			need an alternative logging solution.
		 */
    	var headers:Object = {SOAPAction: "\"\"", Accept: "text/xml", "X-Salesforce-No-500-SC":"true"}; //, "User-Agent": "SFFLEX 1.0"};
    	if (remote != null) {
    		headers["SalesforceProxy-Endpoint"] = remote.url;
    		headers["SalesforceProxy-SID"] = remote.sid;
    	}
    	connection.headers = headers;
    	connection.addEventListener(FaultEvent.FAULT, myFault, true);
    	
    	var x:XML = new XML(envelope.toString());
    	
    	var sendEvent:SendEvent = new SendEvent(SendEvent.SEND_REQUEST, x.toXMLString(), responder);
    	//(responder as AbsSalesforceResponder).sendEvent = sendEvent;
    	var token:AsyncToken = connection.send(envelope.toString());
    	token.addResponder(responder);
    	dispatchEvent(sendEvent);
  	}
  
  public function myFault(event:FaultEvent):void {
  	var temp:FaultEvent = event;
  }
  public function handleResult(event:ResultEvent):void
  {  
    dispatchEvent(event);
  }
  
  public function handleFault(event:FaultEvent):void
  {
    dispatchEvent(event);
  }
}
}