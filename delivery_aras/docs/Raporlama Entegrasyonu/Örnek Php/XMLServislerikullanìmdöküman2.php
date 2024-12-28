<head><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-9" /></head>
<?php      

	#################################################################################################################################
	#																																#
	#  	 XML SERVISLERI PHP KULLANIM ORNEGI																							#
																								#
	#    GetQueryDs i�in yukar�da bulunan charset de�eri T�rk�e karakter sorunu ya�amamak i�in charset=UTF8 olarak de�i�tirmelidir. #
	#    Di�er methodlar i�inse charset=ISO-8859-9 olarak kullan�lmal�d�r.															#
	#																																#
	#################################################################################################################################
	
	class arascargo {
	
	  #De�i�ken tan�mlamalar� burada yap�l�r
	  var $Servis;
	  var $DefaultEncoding = 'ISO-8859-9';
      var $Url = 'http://customerservices.araskargo.com.tr/ArasCargoCustomerIntegrationService/ArasCargoIntegrationService.svc?wsdl';
      var $UserName          = ''; 
      var $Password          = '';
	  var $CustomerCode      = '';
	  var $QueryType 	 	 = '2';
	  var $dtime 	 		 = '02.05.2013';	
	  var $data = array();
      var $Error = array();
	  
	  
	  #SOAP servisi i�in servis client'i burada olu�turulur
		function arascargo(){
			try {
				$return = $this->Servis = new SoapClient($this->Url, array('encoding'=>$this->DefaultEncoding)); 
            } catch(Exception $exp) {
				echo  $this->Error['construct'] = $exp->getMessage();
			}
		}
	  
		#GetQueryDS servisine baglan�p sorgulama yapan fonksiyon 
		function GetDataGetQueryDS(){
			#Servis 2 adet parametre al�r. Bu parametreler burada tan�mlan�r ve de�erleri atan�r.
			$loginInfo         = '<LoginInfo><UserName>' . $this->UserName   . '</UserName><Password>'. $this->Password   .'</Password><CustomerCode>'. $this->CustomerCode   .'</CustomerCode></LoginInfo>';				
			$queryInfo         = '<QueryInfo><QueryType>'. $this->QueryType   .'</QueryType><date>'. $this->dtime   .'</date></QueryInfo>';
			try {
				$return = $this->Servis->GetQueryDS(array("loginInfo"=>$loginInfo,"queryInfo"=>$queryInfo));
				return $return;
			} catch(Exception $exp) {
				echo $this->Error['CreateShipment'] = $exp->getMessage();
			}
		}
		
		#GetQueryXML servisine baglan�p sorgulama yapan fonksiyon 
	    function GetDataGetQueryXML(){
	    #Servis 2 adet parametre al�r. Bu parametreler burada tan�mlan�r ve de�erleri atan�r.
		$loginInfo         = '<LoginInfo><UserName>' . $this->UserName   . '</UserName><Password>'. $this->Password   .'</Password><CustomerCode>'. $this->CustomerCode   .'</CustomerCode></LoginInfo>';				
	    $queryInfo         = '<QueryInfo><QueryType>'. $this->QueryType   .'</QueryType><date>'. $this->dtime   .'</date></QueryInfo>';

		try {
				$return = $this->Servis->GetQueryXML(array("loginInfo"=>$loginInfo,"queryInfo"=>$queryInfo));
				return $return;
			} catch(Exception $exp) {
				echo $this->Error['CreateShipment'] = $exp->getMessage();
			}
		}
		
		#GetQueryJSON servisine baglan�p sorgulama yapan fonksiyon 
	    function GetDataGetQueryJSON(){
			#Servis 2 adet parametre al�r. Bu parametreler burada tan�mlan�r ve de�erleri atan�r.
			$loginInfo         = '<LoginInfo><UserName>' . $this->UserName   . '</UserName><Password>'. $this->Password   .'</Password><CustomerCode>'. $this->CustomerCode   .'</CustomerCode></LoginInfo>';				
			$queryInfo         = '<QueryInfo><QueryType>'. $this->QueryType   .'</QueryType><date>'. $this->dtime   .'</date></QueryInfo>';

			try {
				$return = $this->Servis->GetQueryJSON(array("loginInfo"=>$loginInfo,"queryInfo"=>$queryInfo));
				return $return;
			} catch(Exception $exp) {
				echo $this->Error['CreateShipment'] = $exp->getMessage();
            }
        }
	}
	
	# GetQueryDS servisi burada �a��r�l�yor.
	$aras = new arascargo();  
	$sonuc = $aras->GetDataGetQueryDS();
	ResponseArray($sonuc);	 
	 
	#GetQueryXML servisi burada �a��r�l�yor
	$sonuc = $aras->GetDataGetQueryXML();
	ResponseArray($sonuc);
	 
	#GetQueryJSON servisi burada �a��r�l�yor
	$sonuc = $aras->GetDataGetQueryJSON();
	ResponseArray($sonuc);
	   
	#D�nen sonu�lar� ekrana yazd�r�r
	function ResponseArray($array){
		echo '<pre>';
        print_r($array);
        echo '</pre>';
	}
?>