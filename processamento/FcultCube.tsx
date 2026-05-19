import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

type Props = {
  title: string;
  description?: string;
  action?: string;
  badge?: number | string;
  icon?: React.ReactNode;
  children?: React.ReactNode;
  onPress?: () => void;
};

export default function FcultCube({
  title,
  description,
  action = "Ver",
  badge,
  icon,
  children,
  onPress,
}: Props) {
  return (
    <Pressable style={styles.card} onPress={onPress}>
      {badge ? (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{badge}</Text>
        </View>
      ) : null}

      {icon ? <View style={styles.iconBox}>{icon}</View> : null}

      <View style={styles.textBlock}>
        <Text style={styles.title}>{title}</Text>

        {description ? (
          <Text style={styles.description}>{description}</Text>
        ) : null}

        {children}
      </View>

      <View style={styles.button}>
        <Text style={styles.buttonText}>{action}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    height: 400,
    width: 320,
    backgroundColor: "#FFFFFF",
    borderRadius: 38,
    paddingVertical: 42,
    paddingHorizontal: 26,
    alignItems: "center",
    justifyContent: "space-between",
    shadowColor: "#1C1A28",
    shadowOpacity: 0.08,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 10 },
    elevation: 8,
  },

  badge: {
    position: "absolute",
    top: 18,
    right: 18,
    backgroundColor: "#FF6D00",
    minWidth: 24,
    height: 24,
    borderRadius: 12,
    paddingHorizontal: 7,
    alignItems: "center",
    justifyContent: "center",
  },

  badgeText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "900",
  },

  iconBox: {
    width: 116,
    height: 116,
    borderRadius: 30,
    borderWidth: 1,
    borderColor: "#7C4DFF",
    backgroundColor: "#F2EEF8",
    alignItems: "center",
    justifyContent: "center",
  },

  textBlock: {
    alignItems: "center",
  },

  title: {
    fontSize: 25,
    fontWeight: "800",
    color: "#1C1A28",
    textAlign: "center",
    marginBottom: 8,
  },

  description: {
    fontSize: 13,
    lineHeight: 18,
    color: "#5B5868",
    textAlign: "center",
  },

  button: {
    borderWidth: 1,
    borderColor: "#7C4DFF",
    backgroundColor: "transparent",
    paddingVertical: 13,
    paddingHorizontal: 42,
    borderRadius: 16,
  },

  buttonText: {
    color: "#7C4DFF",
    fontSize: 14,
    fontWeight: "800",
  },
});