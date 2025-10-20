#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN 9
#define SS_PIN 10
#define RELAY_PIN 8

MFRC522 rfid(SS_PIN, RST_PIN);

String readSerialLineWithTimeout(unsigned long timeoutMs){
  unsigned long start=millis();
  String s="";
  while(millis()-start<timeoutMs){
    while(Serial.available()){
      char c=Serial.read();
      if(c=='\n') return s;
      if(c!='\r') s+=c;
    }
  }
  return s;
}

void setup(){
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
}

void loop(){
  if(!rfid.PICC_IsNewCardPresent()) return;
  if(!rfid.PICC_ReadCardSerial()) return;
  char buf[4];
  String uidStr="";
  for(byte i=0;i<rfid.uid.size;i++){
    sprintf(buf,"%02X",rfid.uid.uidByte[i]);
    uidStr+=buf;
    if(i<rfid.uid.size-1) uidStr+=' ';
  }
  Serial.print("UID:");
  Serial.println(uidStr);
  String response=readSerialLineWithTimeout(2000);
  response.trim();
  response.toUpperCase();
  if(response=="OK"){
    digitalWrite(RELAY_PIN,HIGH);
    delay(3000);
    digitalWrite(RELAY_PIN,LOW);
  }
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(200);
}
