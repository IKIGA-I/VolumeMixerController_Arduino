// Pin definitions
const int pinCLK = 2;
const int pinDT = 3;
const int pinButton = 4;

int lastCLK;
int currentVolume = 50;  // Starting volume percentage (example)
int selectedApp = 0;     // 0=Master, 1=Spotify, 2=VLC

unsigned long lastButtonPress = 0;
const unsigned long debounceDelay = 200;

void setup() {
  pinMode(pinCLK, INPUT_PULLUP);
  pinMode(pinDT, INPUT_PULLUP);
  pinMode(pinButton, INPUT_PULLUP);

  Serial.begin(9600);
  lastCLK = digitalRead(pinCLK);

  sendAppSelect(); // Send initial app selection to PC
}

void loop() {
  int currentCLK = digitalRead(pinCLK);

  // Rotary encoder rotation detected
  if (currentCLK != lastCLK) {
    if (digitalRead(pinDT) != currentCLK) {
      // Clockwise turn
      currentVolume = constrain(currentVolume + 1, 0, 100);
      sendVolume();
    } else {
      // Counter-clockwise turn
      currentVolume = constrain(currentVolume - 1, 0, 100);
      sendVolume();
    }
  }
  lastCLK = currentCLK;

  // Button press to switch app
  if (digitalRead(pinButton) == LOW) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastButtonPress > debounceDelay) {
      selectedApp = (selectedApp + 1) % 3; // Cycle 0->1->2->0
      sendAppSelect();
      lastButtonPress = currentMillis;
    }
  }
}

// Send current volume to PC
void sendVolume() {
  // Format: VOLUME:<selectedApp>:<volume>\n
  Serial.print("VOLUME:");
  Serial.print(selectedApp);
  Serial.print(":");
  Serial.println(currentVolume);
}

// Send current selected app to PC
void sendAppSelect() {
  // Format: APP:<selectedApp>\n
  Serial.print("APP:");
  Serial.println(selectedApp);
}
